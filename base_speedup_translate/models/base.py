import itertools
import logging

from functools import wraps

from odoo import api, fields, models, tools, exceptions

_logger = logging.getLogger(__name__)


def config_strip(key):
    value = tools.config.get(key)
    if not value or value and not value.strip():
        return []
    return list(set(map(lambda a: a.strip(' "\''), tools.config[key].split(','))))

# TODO: Add in the doc that is required -u
# TODO: Load in a hook
translate_models = config_strip('translate_models')
translate_models_langs = config_strip('translate_models_langs')
translate_models_fields = {}
for translate_model in translate_models:
    key_fields = 'translate_fields_%s' % translate_model.replace('.', '_')
    translate_models_fields[translate_model] = config_strip(key_fields)


class Base(models.AbstractModel):
    _inherit = 'base'
    _translate_fields = None
    # TODO: Check if not exists the field
    # TODO: Check if the field is indexed?
    # TODO: Update the field if the term is translated directly
    # TODO: Delete indexes and columns if they are deleted in configuration file

    @api.model
    def _add_magic_translated_fields(self):
        """Add translation field indexed for models defined in the configuration file
            e.g. translate_models = product.template,res.partner
                 translate_models_langs = es_MX
        """
        # TODO: Update the field if the term is translated directly
        # TODO: Delete indexes and columns if they are deleted in configuration file

        cls = type(self)
        # self._add_magic_translated_fields()
        def get_compute(field_name, new_field_name, lang):
            @api.depends(field_name)
            def compute(self):
                # TODO: What about memory error?
                recs_lang = dict((r['id'], r['name']) for r in self.with_context(lang=lang, i18n_origin=True).read(['id', 'name']))
                for rec in self:
                    rec[new_field_name] = recs_lang[rec.id]
            return compute

        def add(name, field):
            """ add ``field`` with the given ``name`` if it does not exist yet """
            if name not in self._fields:
                self._add_field(name, field)
        translate_models = config_strip('translate_models')
        # import pdb;pdb.set_trace()
        if self._name not in translate_models or not self.env['res.lang']._fields:
            # self.env['res.lang']._fields <- Required for models not loaded
            # TODO: Use directly cr.execute instead
            return
        translate_models_langs = config_strip('translate_models_langs')
        domain = [('code', 'in', translate_models_langs), ('active', '=', True)]
        for lang in self.env['res.lang'].search(domain).mapped('code'):
            # TODO: Check if not exists the field
            # TODO: Check if the field is indexed?
            field_names = translate_models_fields.get(self._name)
            if not field_names:
                # If the model is defined but the fields are not so use all them
                field_names = [name for name, f in self._fields.items() if f.translate]
            for field_name in set(field_names) & set(self._fields):
                field = self._fields[field_name]
                if not field.translate:
                    continue
                new_field_name = "%s_%s" % (field_name, lang.lower())
                if cls._translate_fields is None:
                    cls._translate_fields = {}
                if lang not in cls._translate_fields:
                    # TODO: collections defaultdict?
                    cls._translate_fields[lang] = {}
                if field_name in cls._translate_fields[lang]:
                    continue
                cls._translate_fields[lang][field_name] = new_field_name
                new_method_name = "_compute_%s" % new_field_name
                new_field = field.new(
                    compute=get_compute(field_name, new_field_name, lang),
                    store=True, index=field.index, prefetch=False)
                add(new_field_name, new_field)
                _logger.info("New translation field %s.%s", self._table, new_field_name)
                for model in self._inherits_children:
                    inherit_cls = type(self.env[model])
                    if inherit_cls._translate_fields is None:
                        inherit_cls._translate_fields = {}
                    if lang not in inherit_cls._translate_fields:
                        # TODO: collections defaultdict?
                        inherit_cls._translate_fields[lang] = {}
                    if field_name in inherit_cls._translate_fields[lang]:
                        continue
                    inherit_cls._translate_fields[lang][field_name] = cls._translate_fields[lang][field_name]

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # env['product.template'].with_context(lang='es_MX', prefetch_fields=False).search([('name', 'ilike', 'alojamien')])
        # env['product.template'].with_context(lang='es_MX', prefetch_fields=False).search([('name', 'ilike', 'Hotel'), ('categ_id', '=', 1), ('description_sale', 'ilike', 'Hotel')])
        # [self.env.cr.execute("ALTER TABLE product_template DROP COLUMN IF EXISTS %s" % (column,)) for column in [i for i in self.env['product.template']._fields.keys() if i.endswith('es_mx') or i.endswith('en_us')]]
        # TODO: Check if the field is defined
        # TODO: Change "product_template"."name_es_mx" as "name_es_mx" ->
        #               "product_template"."name_es_mx" as "name" ->
        # TODO: Support "product_id.name" domains
        # TODO: Support product.product search name
        lang = self.env.context.get('lang')
        models = list(set(list(self._inherits.keys()) + [self._name]) & set(translate_models))
        # TODO: Support related fields
        # TODO: Support es_ES using es_* installed
        if models and self._translate_fields and lang in self._translate_fields and args and not self.env.context.get('i18n_origin'):
            new_args = []
            for arg in args:
                if not isinstance(arg, tuple) or len(arg) != 3:
                    new_args.append(arg)
                    continue
                for field, new_field in self._translate_fields[lang].items():
                    if field == arg[0]:
                        new_args.append((new_field,) + arg[1:])
                        break
                else:
                    new_args.append(arg)
        else:
            new_args = args
        return super(Base, self)._search(new_args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

    @api.model
    def _generate_translated_field(self, table_alias, field, query):
        lang = self.env.context.get('lang')
        if self._name in translate_models and self._translate_fields and field in (self._translate_fields.get(lang) or {}) and not self.env.context.get('i18n_origin'):
            new_field = self._translate_fields[lang][field]
            return '"%s"."%s"' % (table_alias, new_field)
        return super(Base, self)._generate_translated_field(table_alias, field, query)

    @api.model
    def _generate_order_by(self, order_spec, query):
        res = []
        lang = self.env.context.get('lang')
        # TODO: Check bypass patch of order
        # TODO: Fix is adding the same field 3 times
        if not self.env.context.get('i18n_origin'):
            order_spec = order_spec or self._order
            for order_part in (order_spec and order_spec.split(',') or []):
                for field, new_field in (self._translate_fields and self._translate_fields.get(lang) or {}).items():
                    order_split = order_part.strip().split(' ')
                    order_field = order_split[0].strip()
                    if order_field == field:
                        res.append(order_part.replace(field, new_field))
                        break
                else:
                    res.append(order_part)
            order_spec = ','.join(res)
        return super(Base, self)._generate_order_by(order_spec, query)

    @api.model
    def _setup_base(self):
        res = super()._setup_base()
        self._add_magic_translated_fields()
        # cls._proper_fields = set(cls._fields)
        # self._add_inherited_fields()
        # cls.pool.model_cache[cls.__bases__] = cls
        return res
