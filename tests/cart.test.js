import test from 'node:test';
import assert from 'node:assert/strict';
import {total,evidence} from '../dist/cart.js';
test('seeded bug is detected independently of implementation',()=>{assert.equal(total(0,false),2400); assert.equal(evidence(0,false).confirmed,true)});
test('fixed cart is zero after removing the last item',()=>assert.equal(total(0,true),0));
test('normal quantities work in both modes',()=>{for(const fixed of [false,true]) for(const n of [1,2,5]) assert.equal(total(n,fixed),n*2400)});
test('fixed control produces no finding',()=>assert.equal(evidence(0,true).confirmed,false));
