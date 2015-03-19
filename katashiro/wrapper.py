# -*- coding:utf-8 -*-
from katashiro import logger
from katashiro.domain import S
from collections import defaultdict


class DomainMap(object):
    def __init__(self):
        self.pool = defaultdict(dict)

    def lookup(self, scene=""):
        return Lookup(self, scene=scene)

    def get(self, scene, k):
        return self.pool[scene][k]

    def set(self, scene, k, v):
        self.pool[scene][k] = v


class Wrapper(object):
    @property
    def metadata(self):
        return self.domain.metadata

    def __getitem__(self, k):
        return self.domain.metadata.get(k)

    def __repr__(self):
        return "<{} domain={!r} at {}>".format(self.__class__.__name__, self.domain.id, hex(id(self)))


class FieldWrapper(Wrapper):
    def __init__(self, value, domain):
        self.value = value
        self.domain = domain

    def __str__(self):
        return self.serialize()

    def serialize(self):
        fn = self[S.serialize]
        if fn is not None:
            return fn(self.value)
        else:
            return str(self.value)

    def deserialize(self):
        fn = self[S.deserialize]
        if fn is not None:
            return fn(self.value)
        return self.value

    def __repr__(self):
        return "<{} domain={!r} at {}>".format(self.__class__.__name__, self.domain.id, hex(id(self)))


class ModelWrapper(Wrapper):
    def __init__(self, lookup, value, domain):
        self.value = value
        self.domain = domain
        self._children = {}
        self.lookup = lookup

    @property
    def metadata(self):
        return self.domain.metadata

    def __getitem__(self, k):
        return self.domain.metadata[k]

    def __getattr__(self, attrname):
        try:
            return self._children[attrname]
        except KeyError:
            subdomain = self.lookup.lookup(self.value, self.domain, attrname)
            subvalue = getattr(self.value, attrname)
            subwrapper = self.lookup.create_wrapper(subvalue, subdomain)
            self._children[attrname] = subwrapper
            return subwrapper


class ModelSeqWrapper(Wrapper):
    def __init__(self, lookup, seq, domain):
        self.lookup = lookup
        self.seq = seq
        self.domain = domain
        self._children = {}

    def __iter__(self):
        for ob in self.seq:
            yield self.get_child_wrapper(ob)

    def __getitem__(self, k):
        if isinstance(k, int):
            logger.warn("model seq wrapper: no longer support index access.")
            return self.get_child_wrapper(self.sec[k])
        else:
            return super(ModelSeqWrapper, self).__getitem__(k)

    def get_child_wrapper(self, ob):
        try:
            return self._children[ob]
        except KeyError:
            subwrapper = self.lookup.create_wrapper(ob, self.domain.child_domain)
            self._children[ob] = subwrapper
            return subwrapper


class Lookup(object):
    wrapper_factory = ModelWrapper
    seq_wrapper_factory = ModelSeqWrapper
    field_wrapper_factory = FieldWrapper

    def __init__(self, domain_map, scene=""):
        self.domain_map = domain_map
        self.scene = scene

    def create_wrapper(self, ob, domain):
        if domain.manager.is_atom(domain):
            return self.field_wrapper_factory(ob, domain)
        elif domain.manager.is_seq(domain):
            return self.seq_wrapper_factory(self, ob, domain)
        else:
            return self.wrapper_factory(self, ob, domain)

    def lookup(self, ob, domain, attrname):
        k = (ob.__class__, attrname)
        try:
            return self.domain_map.get(self.scene, k)
        except KeyError:
            return self.construct(ob, domain, attrname, k)

    def construct(self, ob, domain, attrname, k):
        logger.debug("construct domain: attrname=%s", attrname)
        if attrname in domain:
            subdomain = getattr(domain, attrname)
        else:
            subdomain = self._construct(ob, attrname)
        self.domain_map.set(self.scene, k, subdomain)
        return subdomain

    def _construct(self, ob, attrname):
        raise AttributeError(attrname)

    def __call__(self, ob, domain):
        self.domain_map.set(self.scene, (ob, None), domain)
        return ModelWrapper(self, ob, domain)


if __name__ == "__main__":
    class Person(object):
        def __init__(self, name, age):
            self.name = name
            self.age = age

    class Parents(object):
        def __init__(self, father, mother):
            self.father = father
            self.mother = mother

    class Family(object):
        def __init__(self, father, mother, children):
            self.father = father
            self.mother = mother
            self.children = children

    from katashiro import Domain, Atom, domain, Seq
    PersonDomain = Domain("person") + Atom("name", {"doc": "Name"}) + Atom("age", {"doc": "Age"})
    ParentsDomain = domain("parents", [("father", PersonDomain), ("mother", PersonDomain)])
    familyDomain = Domain("family", [ParentsDomain.mother, ParentsDomain.father, Seq("children", [PersonDomain])])

    dm = DomainMap()
    lookup = dm.lookup()

    parents = Parents(Person("foo", 20), Person("bar", 20))
    wrapper = lookup(parents, ParentsDomain)
    # many to one
    print("{} - {}".format(wrapper.father.name["doc"], wrapper.father.name))
    print("{} - {}".format(wrapper.father.age["doc"], wrapper.father.age))

    family = Family(Person("foo", 20), Person("bar", 20), [Person("a", 1), Person("b", 2)])
    wrapper = lookup(family, familyDomain)
    for child in wrapper.children:
        print(child.name)
