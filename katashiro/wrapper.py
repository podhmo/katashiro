# -*- coding:utf-8 -*-
from katashiro import logger
from katashiro.domain import S


class FieldWrapper(object):
    def __init__(self, value, domain):
        self.value = value
        self.domain = domain

    def __getitem__(self, k):
        return self.domain.metadata.get(k)

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


class ModelWrapper(object):
    field_wrapper_factory = FieldWrapper

    def __init__(self, value, domain):
        self.value = value
        self.domain = domain
        self.pool = {}

    def __getitem__(self, k):
        return self.domain.metadata[k]

    def construct(self, attrname, value, parent_domain):
        logger.debug("construct domain: attrname=%s", attrname)
        if attrname in parent_domain:
            domain = getattr(parent_domain, attrname)
        else:
            domain = self.construct_domain(attrname, value)
        if domain.manager.is_atom(domain):
            wrapper = self.field_wrapper_factory(value, domain)
        else:
            wrapper = self.__class__(value, domain)
        self.pool[attrname] = wrapper
        return wrapper

    def construct_domain(self, attrname, value):
        raise AttributeError(attrname)

    def __getattr__(self, attrname):
        try:
            return self.pool[attrname]
        except KeyError:
            v = getattr(self.value, attrname)
            return self.construct(attrname, v, self.domain)

    def __repr__(self):
        return "<{} domain={!r} at {}>".format(self.__class__.__name__, self.domain.id, hex(id(self)))


if __name__ == "__main__":
    class Person(object):
        def __init__(self, name, age):
            self.name = name
            self.age = age

    class Parents(object):
        def __init__(self, father, mother):
            self.father = father
            self.mother = mother

    from katashiro import Domain, Atom, domain, Seq
    PersonDomain = Domain("person") + Atom("name", {"doc": "Name"}) + Atom("age", {"doc": "Age"})
    ParentsDomain = domain("parents", [("father", PersonDomain), ("mother", PersonDomain)])
    parents = Parents(Person("foo", 20), Person("bar", 20))
    family = Domain("family", [Seq("children", [PersonDomain])]) + ParentsDomain
    print(family)
    wrapper = ModelWrapper(parents, ParentsDomain)
    print("{} - {}".format(wrapper.father.name["doc"], wrapper.father.name))
    print("{} - {}".format(wrapper.father.age["doc"], wrapper.father.age))
    print(wrapper.father.name)
    print(wrapper.mother)
