from katashiro import DomainMeta, Attribute, Sequence, domain


class Person(metaclass=DomainMeta):
    name = Attribute(label="名前")
    age = Attribute(label="年齢")

print(Person)
print(domain("person", ["name", "age"]))


class Family(metaclass=DomainMeta):
    father = Attribute(Person)
    mother = Attribute(Person)
    children = Sequence(Person)

print(Family)


class Odd(metaclass=DomainMeta):
    prev = Attribute("Even")
    next = Attribute("Even")


class Even(metaclass=DomainMeta):
    prev = Attribute("Odd")
    next = Attribute("Odd")


class User(metaclass=DomainMeta):
    following = Sequence("User")
    followers = Sequence("User")

print(User.following.User.following.User.following.User.followers)
print(User)

if __name__ == "__main__":
    from katashiro.wrapper import DomainMap

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

    class PersonDomain(metaclass=DomainMeta):
        name = Attribute(doc="Name")
        age = Attribute(doc="Age")

    class ParentsDomain(metaclass=DomainMeta):
        father = Attribute(PersonDomain)
        mother = Attribute(PersonDomain)

    class FamilyDomain(metaclass=DomainMeta):
        father = Attribute(PersonDomain)
        mother = Attribute(PersonDomain)
        children = Sequence(PersonDomain)

    dm = DomainMap()
    lookup = dm.lookup()

    parents = Parents(Person("foo", 20), Person("bar", 20))
    wrapper = lookup(parents, ParentsDomain)
    # many to one
    print("{} - {}".format(wrapper.father.name["doc"], wrapper.father.name))
    print("{} - {}".format(wrapper.father.age["doc"], wrapper.father.age))

    family = Family(Person("foo", 20), Person("bar", 20), [Person("a", 1), Person("b", 2)])
    wrapper = lookup(family, FamilyDomain)
    for child in wrapper.children:
        print(child.name)
