import asyncio
import json
import os
import unittest
from unittest.mock import patch
from worker.policy import OpenAIPolicy, OfflinePolicy, parse_response, validate_decision

STATE={'quantity':1,'total_cents':2400,'displayed_total':'$24.00','enabled_buttons':['Add item','Remove item','Reset cart']}
DECISION={'type':'click','name':'Remove item','summary':'Check the empty cart.'}

def response(content=None):
    return {'status':'completed','output':[{'type':'message','content':content or [{'type':'output_text','text':json.dumps(DECISION)}]}],'usage':{'input_tokens':100,'output_tokens':20}}

class PolicyTests(unittest.TestCase):
    def test_valid_action(self):self.assertEqual(validate_decision(DECISION,STATE),DECISION)
    def test_disabled_button_rejected(self):
        with self.assertRaises(ValueError):validate_decision(DECISION,{**STATE,'enabled_buttons':['Add item']})
    def test_arbitrary_code_and_extra_fields_rejected(self):
        for value in [{**DECISION,'type':'eval'}, {**DECISION,'code':'alert(1)'}, {**DECISION,'name':[]}]:
            with self.assertRaises(ValueError):validate_decision(value,STATE)
    def test_stop_requires_empty_target(self):
        with self.assertRaises(ValueError):validate_decision({**DECISION,'type':'stop'},STATE)
    def test_refusal_is_error(self):
        with self.assertRaises(ValueError):parse_response(response([{'type':'refusal','refusal':'No'}]))
    def test_incomplete_is_error(self):
        with self.assertRaises(ValueError):parse_response({**response(),'status':'incomplete'})
    def test_malformed_json_is_error(self):
        with self.assertRaises(ValueError):parse_response(response([{'type':'output_text','text':'not JSON'}]))
    def test_missing_key_does_not_fall_back(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'no offline fallback'):OpenAIPolicy('test-model')
    def test_offline_policy_uses_state(self):
        policy=OfflinePolicy()
        self.assertEqual(asyncio.run(policy.choose(STATE,[]))['name'],'Add item')
        self.assertEqual(asyncio.run(policy.choose({**STATE,'quantity':0},[]))['type'],'stop')
        self.assertEqual(policy.requests,0)
    def test_api_request_and_usage_with_mocked_transport(self):
        class Reply:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps(response()).encode()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-placeholder'}):
            policy=OpenAIPolicy('test-model')
            with patch('urllib.request.urlopen',return_value=Reply()) as request:
                self.assertEqual(asyncio.run(policy.choose(STATE,[])),DECISION)
                payload=json.loads(request.call_args.args[0].data)
                self.assertFalse(payload['store'])
                self.assertEqual(payload['text']['format']['type'],'json_schema')
                self.assertEqual(set(json.loads(payload['input'])),{'state','history'})
                self.assertNotIn('test-placeholder',json.dumps(payload))
                self.assertEqual(policy.usage,{'input_tokens':100,'output_tokens':20})
                self.assertEqual(policy.requests,1)
