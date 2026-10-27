import unittest
from worker.core import check_contract, observation, validate_actions, validate_target, verdict
from worker.run import regression_source


def completed(status, actual=0):
    contract = {'status':status, 'contract':'empty-cart-zero-total'}
    if status != 'not_applicable':
        contract.update(expected_cents=0, actual_cents=actual)
    return {'status':'completed', 'contract':contract}

class WorkerTests(unittest.TestCase):
    def test_independent_contract(self):
        self.assertEqual(check_contract(observation('0','$24.00'))['status'],'fail')
        self.assertEqual(check_contract(observation('0','$0.00'))['status'],'pass')
        self.assertEqual(check_contract(observation('1','$24.00'))['status'],'not_applicable')
    def test_missing_or_malformed_ui_is_not_a_finding(self):
        for q, t in [('',''),('0','error'),('-1','$24.00'),('0','$NaN')]:
            with self.assertRaises(ValueError): observation(q,t)
    def test_confirm_requires_matching_failures(self):
        self.assertEqual(verdict(completed('fail',2400),completed('fail',2400)),'confirmed')
        self.assertEqual(verdict(completed('fail',2400),completed('fail',4800)),'not_reproduced')
    def test_non_reproduction(self):
        self.assertEqual(verdict(completed('fail',2400),completed('pass')),'not_reproduced')
    def test_clean_control(self):
        self.assertEqual(verdict(completed('pass'),completed('pass')),'passed')
    def test_error_never_becomes_confirmed(self):
        self.assertEqual(verdict(completed('fail',2400),{'status':'error'}),'runner_error')
    def test_unexercised_contract_is_inconclusive(self):
        self.assertEqual(verdict(completed('not_applicable'),completed('not_applicable')),'inconclusive')
    def test_action_validation(self):
        for actions in [[],[{'type':'eval','name':'Remove item'}],[{'type':'click','name':'Buy'}], [{'type':'click','name':'Add item'}]*13]:
            with self.assertRaises(ValueError): validate_actions(actions)
    def test_target_validation(self):
        for url in ['https://example.com','http://localhost@evil.com','http://localhost/?mode=fixed','file:///tmp/x']:
            with self.assertRaises(ValueError): validate_target(url)
        self.assertEqual(validate_target('http://localhost:8000/'),'http://localhost:8000')
    def test_export_is_valid_python(self):
        compile(regression_source('http://localhost:8000/?mode=buggy',[{'type':'click','name':'Remove item'}]),'regression.py','exec')

if __name__ == '__main__': unittest.main()
