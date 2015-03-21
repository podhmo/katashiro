# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from .domain import Manager, _Seq, _Domain, _Atom
from .wrapper import DomainMap
from .declarative import Translator


default_domain_manager = Manager(_Seq, _Domain, _Atom)
default_translator = Translator(default_domain_manager)
default_domain_map = DomainMap()
Domain = default_domain_manager.Domain
Atom = default_domain_manager.Atom
Seq = default_domain_manager.Seq
domain = default_domain_manager.shortcut
Attribute = default_translator.Attribute
Sequence = default_translator.Seq
DomainMeta = default_translator.DomainMeta
