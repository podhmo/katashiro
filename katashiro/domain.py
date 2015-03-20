# -*- coding:utf-8 -*-
from katashiro.exceptions import Conflict
from katashiro.langhelpers import reify


class Manager(object):
    fields_factory = list

    def __init__(self, seq_factory, domain_factory, atom_factory):
        self.seq_factory = seq_factory
        self.domain_factory = domain_factory
        self.atom_factory = atom_factory

    def compose(self, x, y):
        x_fields, x_metadata = x.decompose()
        y_fields, y_metadata = y.decompose()
        self.check_fields_conflict(x_fields, y_fields, x, y)
        self._extend_fields(x_fields, y_fields)
        metadata = {x.id: x_metadata, y.id: y_metadata}
        return self.domain_factory(self, x.id, x_fields, metadata)

    def check_fields_conflict(self, x_fields, y_fields, x, y):
        candidates = set(f.id for f in x_fields)
        for f in y_fields:
            if f.id in candidates:
                raise Conflict("{} of ({} and {})".format(f.id, x, y))

    def child_id(self, x, subid):
        if hasattr(x, "_child_id"):
            return x._child_id(subid)
        else:
            return "{}.{}".format(x.id, subid)

    def Domain(self, *args, **kwargs):
        return self.domain_factory(self, *args, **kwargs)

    def Atom(self, id, *args, **kwargs):
        return self.atom_factory(self, id, *args, **kwargs)

    def Seq(self, id, *args, **kwargs):
        return self.seq_factory(self, id, *args, **kwargs)

    def _include_deep(self, domain, predicate):
        if self.is_atom(domain):
            if predicate(domain):
                return domain
            else:
                return None
        else:
            fields, metadata = domain.decompose()
            new_fields = self.fields_factory()
            new_metadata = {}
            new_domain = self.Domain(domain.id, new_fields, new_metadata)
            for f in fields:
                v = self._include_deep(f, predicate)
                if v is not None:
                    self._add_field(new_domain, v)
                    if v.id in metadata:
                        self._add_metadata(new_domain, metadata[v.id])
            return new_domain

    def _include_shallow(self, domain, predicate):
        fields, metadata = domain.decompose()
        new_fields = self.fields_factory()
        new_metadata = {}
        new_domain = self.Domain(domain.id, new_fields, new_metadata)
        for f in fields:
            if predicate(f):
                self._add_field(new_domain, f)
            if f.id in metadata:
                self._add_metadata(new_domain, metadata[f.id])
        return new_domain

    def include(self, domain, predicate, deep=True):
        if deep:
            return self._include_deep(domain, predicate)
        else:
            return self._include_shallow(domain, predicate)

    def exclude(self, domain, predicate, deep=True):
        return self.include(domain, lambda d: not(predicate(d)), deep=deep)

    def rename(self, domain, names):
        if self.is_atom(domain):
            if domain.id in names:
                return self.Atom(names[domain.id], domain.metadata.copy())
            else:
                return domain
        else:
            fields = [self.rename(f, names) for f in domain.fields]
            metadata = domain.metadata.copy()
            return self.Domain(names.get(domain.id, domain.id), fields, metadata)

    def _extend_fields(self, fields0, fields1):
        fields0.extend(fields1)

    def _add_field(self, domain, field):
        domain.fields.append(field)

    def _add_metadata(self, domain, k, v):
        domain.metadata[k] = v

    def is_seq_metadata(self, metadata):
        return metadata and metadata.get("datatype") == "seq"  # xxx:

    def as_seq_metadata(self, metadata):
        metadata["datatype"] = "seq"  # xxx:
        return metadata

    def is_seq(self, child):
        return self.is_seq_metadata(child.metadata)

    def is_atom(self, child):
        return not hasattr(child, "fields")

    def is_domain(self, child):
        return hasattr(child, "decompose")

    def shortcut(self, id, attributes, metadata=None):
        domain = self.Domain(id, self.fields_factory(), metadata)
        for child in attributes:
            if isinstance(child, (list, tuple)):
                if len(child) < 3:
                    if isinstance(child[1], (list, tuple)):
                        # id, fields
                        self._add_field(domain, self.shortcut(child[0], child[1]))
                    else:
                        sub_id = child[0]
                        sub_fields, sub_metadata = child[1].decompose()
                        self._add_field(domain, self.Domain(sub_id, sub_fields, sub_metadata))
                else:
                    # id, fields, metadata
                    self._add_field(domain, self.shortcut(child[0], child[1], child[2]))
            else:
                # id
                self._add_field(domain, self.Atom(child))
        # xxx:
        return self.Seq(id, domain.fields, domain.metadata) if self.is_seq_metadata(domain.metadata) else domain


missing = object()


class _Domain(object):
    def __init__(self, manager, id, fields=None, metadata=None):
        self.manager = manager
        self.id = id
        self.fields = fields or manager.fields_factory()
        self.metadata = metadata or {}

    def decompose(self):
        return self.fields.copy(), self.metadata.copy()

    def __add__(self, other):
        return self.manager.compose(self, other)

    def include(self, predicate, deep=True):
        return self.manager.include(self, predicate, deep=deep)

    def exclude(self, predicate, deep=True):
        return self.manager.exclude(self, predicate, deep=deep)

    def cut(self, ids):
        return self.manager.exclude(self, lambda d: d.id in ids, deep=False)

    def only(self, ids):
        return self.manager.include(self, lambda d: d.id in ids, deep=False)

    # @reify
    # def field_dict(self):
    #     return {f.id: f for f in self.fields}

    # def __getattr__(self, id):
    #     try:
    #         return self.field_dict[id]
    #     except KeyError:
    #         raise AttributeError(id)

    # def __contains__(self, id):
    #     return id in self.field_dict

    @reify
    def field_dict(self):
        return {}

    def __getattr__(self, id):
        try:
            return self.field_dict[id]
        except KeyError:
            for f in self.fields:
                self.field_dict[f.id] = f
                if id == f.id:
                    if hasattr(f, "_swap"):
                        return f._swap()
                    return f
        raise AttributeError(id)

    def __contains__(self, id):
        try:
            return self.field_dict[id]
        except KeyError:
            for f in self.fields:
                self.field_dict[f.id] = f
                if id == f.id:
                    return True
        return id in self.field_dict

    def rename(self, **names):
        return self.manager.rename(self, names)

    @property
    def declared(self):
        s = []
        manager = self.manager
        for f in self.fields:
            if hasattr(f, "declared"):
                for subid in f.declared:
                    s.append(manager.child_id(f, subid))
            else:
                s.append(f.id)
        return s

    def __repr__(self):
        fmt = '<{} id={}, declared={!r} at {}>'
        return fmt.format(self.__class__.__name__,
                          self.id,
                          self.declared,
                          hex(id(self)))


class _Atom(object):
    def __init__(self, manager, id, metadata=None):
        self.manager = manager
        self.id = id
        self.metadata = metadata or {}

    def decompose(self):
        return [self], self.metadata.copy()

    def __repr__(self):
        fmt = '<{} id={}, at {}>'
        return fmt.format(self.__class__.__name__,
                          self.id,
                          hex(id(self)))


class _Seq(_Domain):
    def __init__(self, manager, id, fields=None, metadata=None):
        self.manager = manager
        self.id = id
        assert len(fields) == 1
        self.fields = fields or manager.field_dict()
        # xxx:
        if metadata:
            assert manager.is_seq_metadata(metadata)
        self.metadata = metadata or {"datatype": "seq"}

    @property
    def child_domain(self):
        return self.fields[0]

    def _child_id(self, subid):
        return "{}[].{}".format(self.id, subid.split(".", 1)[1])

    def __repr__(self):
        fmt = '<{} id={}[], declared={!r} at {}>'
        return fmt.format(self.__class__.__name__,
                          self.id,
                          self.declared,
                          hex(id(self)))


class Symbol:
    datatype = "datatype"
    serialize = "serialize"
    deserialize = "deserialize"


class Type:
    str = "str"
    int = "int"
    datetime = "datetime"


class SetManager(Manager):
    fields_factory = set

    def _add_field(self, domain, field):
        domain.fields.add(field)

    def _extend_fields(self, fields0, fields1):
        fields0.update(fields1)


S = Symbol
default_domain_manager = Manager(_Seq, _Domain, _Atom)
Domain = default_domain_manager.Domain
Atom = default_domain_manager.Atom
Seq = default_domain_manager.Seq
domain = default_domain_manager.shortcut


if __name__ == "__main__":
    # print(Domain("Foo") + Atom("x") + Atom("y"))
    # print(Domain("Foo", [(Domain("Left") + Atom("value")), (Domain("Right") + Atom("value"))]))
    # print(Seq("People", [Domain("Person") + Atom("name") + Atom("age")]))
    # print(Domain("School", [Atom("name"), Seq("strudents", [Domain("student") + Atom("name") + Atom("grade")])]))

    print(domain("foo", ["x", "y"]))
    print(domain("foo", [("left", ["value"]), ("right", ["value"])]))
    print(domain("people", [("person", ["name", "age"])], {"datatype": "seq"}))
    print(domain("school", ["name", ("students", [("student", ["name", "age"])], {"datatype": "seq"})]))
    print(domain("person", ["name", "age"]) + domain("address", ["tel", "address0", "address1"]))
    print(domain("person", ["name", "age", "birth"]))
    print(domain("person", ["name", "age", "birth"]).cut("birth"))

    Person = (Domain("person")
              + Atom("name", {"datatype": Type.str})
              + Atom("age", {"datatype": Type.int})
              + Atom("birth", {"datatype": Type.datetime}))
    print(Person)
    Parents = domain("parents", [("mother", Person), ("father", Person)])
    print(Parents.exclude(lambda d: d.metadata.get("datatype") == Type.datetime))
    print(Parents.rename(mother="M", father="F"))
    Family = Domain("family", [Parents.mother, Parents.father, Seq("children", [Person])])
    print(Family.children.person.name)
