import unittest
import random
import math

import behaviours

class Testbehaviours(unittest.TestCase):
	def test_do(self):
		target = []
		tree = behaviours.do("call_it", lambda state: state.append(True))
		running, success = tree.tick(target)

		self.assertEqual(running, False)
		self.assertEqual(success, True)
		self.assertEqual(target, [True])

	def test_run(self):
		target = []
		tree = behaviours.run("call_it", lambda state: state.append(True))
		
		running, success = tree.tick(target)
		self.assertEqual(running, True)
		self.assertEqual(target, [True])

		running, success = tree.tick(target)
		self.assertEqual(running, False)
		self.assertEqual(success, True)
		self.assertEqual(target, [True])

	def test_do_fail(self):
		tree = behaviours.do("call_it", lambda state: 1/0)
		running, success = tree.tick()

		self.assertEqual(running, False)
		self.assertEqual(success, False)
		
	def test_eval(self):
		tree = behaviours.evalb("call it", lambda state: True)
		running, success = tree.tick()

		self.assertEqual(running, False)
		self.assertEqual(success, True)
		
	def test_eval_fail(self):
		tree = behaviours.evalb("call it", lambda state: False)
		running, success = tree.tick()

		self.assertEqual(running, False)
		self.assertEqual(success, False)
		
	def test_wait(self):
		tree = behaviours.wait(2)
		running, success = tree.tick()
		self.assertEqual(running, True)
		running, success = tree.tick()
		self.assertEqual(running, True)
		running, success = tree.tick()
		self.assertEqual(running, False)
		self.assertEqual(success, True)
		
	def test_sequence(self):
		target = []
		tree = behaviours.sequence("append two",
			behaviours.do("call it1", lambda state: state.append(1)),
			behaviours.wait(1),
			behaviours.do("call it2", lambda state: state.append(2)),
		)

		running, success = tree.tick(target)
		self.assertEqual(running, True)
		self.assertEqual(target, [1])

		running, success = tree.tick(target)
		self.assertEqual(running, False)
		self.assertEqual(success, True)
		self.assertEqual(target, [1, 2])

	def test_sequence_fail(self):
		target = []
		tree = behaviours.sequence("append two",
			behaviours.evalb("fail", lambda s: False),
			behaviours.do("call it", lambda s: target.append(2)),
		)

		running, success = tree.tick()
		self.assertEqual(running, False)
		self.assertEqual(success, False)

	def test_select(self):
		tree = behaviours.select("pick one",
			behaviours.evalb("fail", lambda state: False),
			behaviours.wait(1),
		)

		running, success = tree.tick()
		self.assertEqual(running, True)
		running, success = tree.tick()
		self.assertEqual(running, False)
		self.assertEqual(success, True)

	def test_select_fail(self):
		tree = behaviours.select("pick one",
			behaviours.evalb("fail", lambda s: False),
			behaviours.evalb("fail", lambda s: False),
		)

		running, success = tree.tick()
		self.assertEqual(running, False)
		self.assertEqual(success, False)
		

	def test_parallel_while(self):
		s = dict(stop=False, count=0)
		tree = behaviours.whileb("repeat while",
			behaviours.evalb("check", lambda state: not state['stop']),
			behaviours.do("count", lambda state: state.__setitem__("count", state["count"] + 1))
		)
		running, success = tree.tick(s)
		self.assertEqual(running, True)
		self.assertEqual(s['count'], 1)

		running, success = tree.tick(s)
		self.assertEqual(running, True)
		self.assertEqual(s['count'], 2)
		
		s['stop'] = True
		running, success = tree.tick(s)
		self.assertEqual(running, False)
		self.assertEqual(success, True)
		self.assertEqual(s['count'], 3)
		

	def test_parallel_until(self):
		s = dict(stop=False, count=0)
		tree = behaviours.untilb("repeat until",
			behaviours.evalb("check", lambda state: state['stop']),
			behaviours.notb(behaviours.do("incr", lambda state: state.__setitem__("count", state["count"] + 1))),
		)
		running, success = tree.tick(s)
		self.assertEqual(running, True)
		self.assertEqual(s['count'], 1)

		running, success = tree.tick(s)
		self.assertEqual(running, True)
		self.assertEqual(s['count'], 2)
		
		s['stop'] = True
		running, success = tree.tick(s)
		self.assertEqual(running, False)
		self.assertEqual(success, True)
		self.assertEqual(s['count'], 3)



	def test_notb(self):
		tree = behaviours.notb(
			behaviours.evalb("check", lambda state: True))
		running, success = tree.tick()
		self.assertEqual(running, False)
		self.assertEqual(success, False)

		tree = behaviours.notb(
			behaviours.evalb("check", lambda state: False))
		running, success = tree.tick()
		self.assertEqual(running, False)
		self.assertEqual(success, True)

	def test_chance(self):
		random.seed(1)
		v = random.random()
		# this p is higher that the 'random' value that will be picked => success
		success_v = math.sqrt(v)
		# this p is lower that the 'random' value that will be picked => fail
		fail_v = v**2

		tree = behaviours.chance(success_v, 
			behaviours.evalb("check", lambda state: True)
		)
		random.seed(1)
		running, success = tree.tick()

		self.assertEqual(running, False)
		self.assertEqual(success, True)

		tree = behaviours.chance(fail_v, 
			behaviours.evalb("check", lambda state: True)
		)

		random.seed(1)
		running, success = tree.tick()

		self.assertEqual(running, False)
		self.assertEqual(success, False)

		random.seed(1)

		tree = behaviours.chance(success_v, 
			behaviours.evalb("check", lambda state: False)
		)
		running, success = tree.tick()

		self.assertEqual(running, False)
		self.assertEqual(success, False)
		
	def test_repeat(self):
		target = []
		tree = behaviours.repeat(behaviours.do("success", lambda state: state.append(True)))
		running, success = tree.tick(target)
		self.assertEqual(running, True)
		self.assertEqual(target, [True])
		running, success = tree.tick(target)
		self.assertEqual(running, True)
		self.assertEqual(target, [True, True])

	def test_conditional(self):
		tree = behaviours.conditional("condition",
			condition=behaviours.evalb("check", lambda state: True),
			true=behaviours.do("exito", lambda state: state.append(True)),
			false=behaviours.do("fail", lambda state: state.append(False)),
		)

		target = []
		running, success = tree.tick(target)
		self.assertEqual(running, False)
		self.assertEqual(success, True)
		self.assertEqual(target, [True])

	def test_conditional_long(self):
		state = dict(target=[], condition=True)
		tree = behaviours.conditional("condition",
			condition=behaviours.evalb("check", lambda state: state['condition']),
			true=behaviours.repeat(behaviours.do("success", lambda state: state['target'].append(True))),
			false=behaviours.repeat(behaviours.do("fail", lambda state: state['target'].append(False))),
		)

		
		running, success = tree.tick(state)
		self.assertEqual(running, True)
		self.assertEqual(state['target'], [True])
		
		running, success = tree.tick(state)
		self.assertEqual(running, True)
		self.assertEqual(state['target'], [True, True])

		state['condition'] = False
		running, success = tree.tick(state)
		self.assertEqual(running, True)
		self.assertEqual(state['target'], [True, True, False])

		state['condition'] = True
		running, success = tree.tick(state)
		self.assertEqual(running, True)
		self.assertEqual(state['target'], [True, True, False, True])

