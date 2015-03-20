# -*- coding:utf-8 -*-
from katashiro.domain import domain, default_domain_manager
from katashiro.langhelpers import reify


class Counter(object):
    def __init__(self, i):
        self.i = i

    def __call__(self):
        v = self.i
        self.i += 1
        return v

C = Counter(0)


class _Attribute(object):
    def __init__(self, translator, domain=None, **metadata):
        self.translator = translator
        self.domain = domain
        self._count = C()
        self.metadata = metadata


class _Alias(object):
    def __init__(self, translator, name, domain_name, metadata):
        self.translator = translator
        self.name = name
        self.domain_name = domain_name
        self.metadata = metadata
        self.is_seq = self.translator.manager.is_seq_metadata(metadata)

    @property
    def id(self):
        return self.name

    @reify
    def domain(self):
        domain = self.translator.domains[self.domain_name]
        if not self.is_seq:
            return self.translator.manager.Domain(self.name, *domain.decompose())
        else:
            domain = self.translator.manager.Domain(self.domain_name, *domain.decompose())
            return self.translator.manager.Seq(self.name, [domain], metadata=self.metadata)

    def _swap(self):
        return self.domain

    def _child_id(self, subid):
        if self.is_seq:
            return "{}[].{}".format(self.id, subid.split(".", 1)[1])
        else:
            return"{}.{}".format(self.id, subid)


class Translator(object):
    def __init__(self, manager):
        self.manager = manager
        self.domains = {}

    def Attribute(self, *args, **kwargs):
        return _Attribute(self, *args, **kwargs)

    def Seq(self, *args, **kwargs):
        self.manager.as_seq_metadata(kwargs)
        return _Attribute(self, *args, **kwargs)

    def is_attribute(self, attribute):
        return isinstance(attribute, _Attribute)

    def is_atom(self, attribute):
        return attribute.domain is None

    def is_domain_name(self, attribute):
        return isinstance(attribute.domain, str)

    def on_attribute(self, name, attribute):
        if self.is_atom(attribute):
            return self.on_atom(name, attribute)
        elif self.is_domain_name(attribute):
            return self.on_domain_name(name, attribute)
        else:
            return self.on_domain(name, attribute)

    def on_domain(self, name, attribute):
        fields, metadata = attribute.domain.decompose()
        metadata.update(attribute.metadata)
        if self.manager.is_seq_metadata(metadata):
            domain = self.manager.Seq(name, [self.manager.Domain(name, fields, metadata)])
        else:
            domain = self.manager.Domain(name, fields, metadata)
        self.domains[name] = domain
        return domain

    def on_domain_name(self, name, attribute):
        domain_name = attribute.domain
        # attribute.domain = self.domains[domain_name]
        alias = _Alias(self, name, domain_name, attribute.metadata)
        self.domains[name] = alias
        return alias

    def on_atom(self, name, attribute):
        return self.manager.Atom(name, attribute.metadata)

    def DomainMeta(self, name, bases, attrs):
        domain = self.manager.Domain(name)
        self.domains[name] = domain
        attributes = [(k, v) for k, v in attrs.items() if self.is_attribute(v)]
        for k, v in sorted(attributes, key=lambda p: p[1]._count):
            field = self.on_attribute(k, v)
            self.manager._add_field(domain, field)
        return domain


default_translator = Translator(default_domain_manager)
Attribute = default_translator.Attribute
Seq = default_translator.Seq
DomainMeta = default_translator.DomainMeta


class Person(metaclass=DomainMeta):
    name = Attribute(label="名前")
    age = Attribute(label="年齢")

print(Person)
print(domain("person", ["name", "age"]))


class Family(metaclass=DomainMeta):
    father = Attribute(Person)
    mother = Attribute(Person)
    children = Seq(Person)

print(Family)


class Odd(metaclass=DomainMeta):
    prev = Attribute("Even")
    next = Attribute("Even")


class Even(metaclass=DomainMeta):
    prev = Attribute("Odd")
    next = Attribute("Odd")


class Address(metaclass=DomainMeta):
    id = Attribute()
    street = Attribute()
    city = Attribute()
    latitude = Attribute()
    logitude = Attribute()
    person = Attribute("Person")


class Group(metaclass=DomainMeta):
    identifier = Attribute()
    leader = Attribute("Person")
    executive = Seq("Person")
    members = Seq("Person")


class Person(metaclass=DomainMeta):
    id = Attribute()
    name = Attribute()
    surname = Attribute()
    gender = Attribute()
    birthday = Attribute()
    age = Attribute()
    address = Attribute(Address)


class Account(metaclass=DomainMeta):
    email = Attribute()
    enabled = Attribute()
    created = Attribute()
    timeout = Attribute()
    person = Attribute(Person)

print(Group)
print(Group.members.Person.name)
