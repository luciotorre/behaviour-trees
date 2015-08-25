import random
import logging

log = logging.getLogger('behaviours')

class Node(object):
	def __init__(self, name, klass, children, **kwargs):
		self.name = name
		self.klass = klass
		self.children = list(children)
		self.kwargs = kwargs

		self.parent = None
		self.state = None

		for child in children:
			child.set_parent(self)

	def set_parent(self, parent):
		self.parent = parent

	def fullname(self):
		pre = ""
		if self.parent is not None:
			pre = self.parent.fullname() + "."
		return pre + self.name.replace(" ", "_")

	def enter(self, state):
		self.state = self.klass(self)

	def exit(self, state):
		self.state.exit(state)
		self.state = None

	def tick(self, state=None):
		if self.state is None:
			log.debug("[ENTER] {}".format(self.fullname()))
			self.enter(state)

		running, success = self.state.tick(state)
		if not running:
			log.debug("[EXIT] {} : {}".format(self.fullname(), success))
			self.exit(state)

		return running, success


class Behaviour(object):
	def __init__(self, node):
		self.node = node

	def tick(self, state):
		raise NotImplementedError()

	def exit(self, state):
		pass


class Do(Behaviour):
	def tick(self, state):
		try:
			self.node.kwargs['what'](state)
		except Exception as e:
			logging.exception(e) 
			return False, False
		return False, True

def do(name, what):
	"""
	Executes the callable what(state)
	Will finish and succeed immediately
	"""
	return Node(name, Do, [], what=what)

class Run(Behaviour):
	def __init__(self, node):
		super(Run, self).__init__(node)
		self.wait = True
		self.rv = None

	def tick(self, state):
		if self.wait:
			self.rv = self.node.kwargs['what'](state)
			self.wait = False
			return True, True
		return False, True

def run(name, what):
	"""
	Executes the callable what(state)
	Will finish and succeed on the next tick
	"""
	return Node(name, Run, [], what=what)


class Repeat(Behaviour):
	def tick(self, state):
		running, success = self.node.children[0].tick(state)
		if not running and not success:
			return False, False

		return True, True

def repeat(what):
	"""
	Will run the node and restart it every time unless it finishes in error.
	"""
	return Node("repeat", Repeat, [what])

class Chance(Behaviour):
	def __init__(self, node):
		super(Chance, self).__init__(node)
		self.success = random.random() <= node.kwargs['threshold']

	def tick(self, state):
		if not self.success:
			return False, False

		return self.node.children[0].tick(state)


def chance(threshold, what):
	"""
	Will fail with (1-threshold) probability, evaluated in node enter.
	Otherwise it should be the same as a passthrough.
	"""
	return Node("chance({0:.2f})".format(threshold), Chance, [what], threshold=threshold)

class NotB(Behaviour):
	def tick(self, state):
		running, success = self.node.children[0].tick(state)
		if running:
			return True, True
		else:
			return False, not success

def notb(node):
	"""
	Returns the same running status and a negated success value.
	"""
	return Node("not", NotB, [node])


class Wait(Behaviour):
	def __init__(self, node):
		super(Wait, self).__init__(node)
		self.count = self.node.kwargs['steps']

	def tick(self, state):
		if self.count <= 0:
			return False, True

		self.count -= 1
		return True, True

def wait(steps):
	"""
	Runs for steps ticks and then succeeds
	"""
	return Node("wait {}".format(steps), Wait, [], steps=steps)

class EvalB(Behaviour):
	def tick(self, state):
		try:
			rv = self.node.kwargs['what'](state)
		except Exception as e:
			logging.exception(e) 
			return False, False
		return False, bool(rv)

def evalb(name, what):
	"""
	Run what and finish immediately with success == bool(what(state))
	"""
	return Node(name, EvalB, [], what=what)


class Sequence(Behaviour):
	def __init__(self, node):
		super(Sequence, self).__init__(node)
		self.pointer = 0

	def tick(self, state):
		while self.pointer < len(self.node.children):
			
			running, success = self.node.children[self.pointer].tick(state)
			if running:
				return True, success
		
			if not success:
				return False, False

			self.pointer += 1

		return False, success
			

def sequence(name, *children):
	"""
	Run each children after the previous one finished, until one fails, then exit.
	Success value is the AND of all success values of nodes run.
	"""
	return Node(name, Sequence, children)

class Select(Behaviour):
	def __init__(self, node):
		super(Select, self).__init__(node)
		self.pointer = 0

	def tick(self, state):
		while self.pointer < len(self.node.children):
		
			running, success = self.node.children[self.pointer].tick(state)

			if running:
				return True, success
			else:
				if success:
					return False, True

				self.pointer += 1

				
		return False, success
	

def select(name, *children):
	"""
	Run each children after the previous one finished, until one succeeds, then exit.
	Success value is the OR of all success values of nodes run.
	"""
	return Node(name, Select, children)

class UntilB(Behaviour):
		
	def tick(self, state):
		exit = False
		for child in self.node.children:
			running, success = child.tick(state)

			if not running:
				exit = exit or success

		if exit:
			return False, True
		else:
			return True, True
			

def untilb(name, *children):
	"""
	Executes all children in parallel, restarting the finished ones until one child
	finishes with success
	"""
	return Node(name, UntilB, children)

class WhileB(Behaviour):
		
	def tick(self, state):
		repeat = True
		for child in self.node.children:
			running, success = child.tick(state)

			if not running:
				repeat = repeat and success

		if repeat:
			return True, True
		else:
			return False, True
			

def whileb(name, *children):
	"""
	Executes all children in parallel, restarting the finished ones until one child
	finishes with failure
	"""
	return Node(name, WhileB, children)

# anyb, allb, condition
class Conditional(Behaviour):
	def __init__(self, node):
		super(Conditional, self).__init__(node)
		self.last_run = None

	def tick(self, state):
		running, success = self.node.children[0].tick(state)
		if running:
			return True, True

		if success:
			selected = self.node.children[1]
		else:
			selected = self.node.children[2]

		if selected != self.last_run:
			if self.last_run is not None:
				self.last_run.exit(state)
			self.last_run = selected

		return selected.tick(state)

def conditional(name, condition=None, true=None, false=None):
	"""
	In every tick will evaluate the condition and executed the true or false branch
	according to the result value.

	Will enter and exit nodes accordingly.
	"""
	return Node(name, Conditional, [condition, true, false])
		

