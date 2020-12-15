import itertools
import logging

from functools import wraps

from odoo import api, fields, models, tools, exceptions

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = 'base'

    # @api.model
    # def _add_magic_translated_fields(self):
    #     def add(name, field):
    #         """ add ``field`` with the given ``name`` if it does not exist yet """
    #         if name not in self._fields:
    #             self._add_field(name, field)
    #     def config_strip(key):
    #         return list(set(map(lambda a: a.strip(' "\''), (tools.config.get(key) or '').split(','))))
    #     field_type = {'char': fields.Char, 'text': fields.Text}
    #     translate_models = config_strip('translate_models')
    #     if self._name not in translate_models:
    #         return
    #     translate_models_langs = config_strip('translate_models_langs')
    #     domain = [('code', 'in', translate_models_langs), ('active', '=', True)]
    #     for lang in self.env['res.lang'].search(domain).mapped('code'):
    #         # TODO: Check if not exists the field
    #         # TODO: Check if the field is indexed?
    #         for field_name, field in list(self._fields.items()):
    #             if not field.translate:
    #                 continue
    #             try:
    #                 field_type_class = field_type[field.type]
    #             except IndexError:
    #                 continue
    #             if field_name != 'name':
    #                 continue
    #             new_field_name = "%s_%s" % (field_name, lang.lower())
    #             new_method_name = "_compute_%s" % new_field_name
    #             # _logger.warning("field_name %s", field_name)
    #             def _get_method(field_name, new_field_name, lang):
    #                 @api.depends(field_name)
    #                 def _compute_translated_field(self):
    #                     # _logger.info("Computing %s based on %s with lang %s", new_field_name, field_name, lang)
    #                     # import pdb;pdb.set_trace()
    #                     for rec in self.with_context(lang=lang):
    #                         # _logger.info("record %s values of %s:'%s' stored in %s", rec, field_name, rec[field_name], new_field_name)
    #                         # rec[new_field_name] = rec[field_name]
    #                         # _logger.info("Rec %s Value stored in %s: %s", rec, new_field_name, getattr(rec, new_field_name, False))
    #                         # rec.write({new_field_name: rec[field_name]})
    #                         rec.update({new_field_name: rec[field_name]})
    #                         # setattr(rec, new_field_name, rec[field_name])
    #                 return _compute_translated_field

    #             cls = type(self)
    #             # _logger.warning("new method %s for %s lang %s", new_method_name, new_field_name, lang)
    #             new_method = _get_method(field_name, new_field_name, lang)
    #             setattr(cls, new_method_name, new_method)
    #             # setattr(cls, new_method_name, _get_method(field_name, new_field_name, lang))
    #             # self._patch_method(new_method_name, _get_method(field_name, new_field_name, lang))
    #             new_field = field_type_class(automatic=True, index=True, store=True, readonly=True,
    #                                          # compute=getattr(cls, new_method_name))
    #                                          compute=new_method_name)
    #             # new_field.setup_triggers(self._name)
    #             add(new_field_name, new_field)
    #             # self.setup_triggers(self._name)
    #             # _logger.info("New field added %s.%s", self._name, new_field_name)
    #             # recs = self.with_context(active_test=False).search([])
    #             # _logger.info("Re-computing field added %s.%s", self._name, new_field_name)
    #             # def recompute_method(self):
    #             # def recompute(field):
    #             #     _logger.error("Storing computed values of %s", field)
    #             #     recs = self.with_context(active_test=False).search([])
    #             #     recs._recompute_todo(field)
    #             #     # return recompute
    #             # _logger.error("aqui")
    #             # _logger.error("ANTES queue %s", self.pool._post_init_queue)
    #             # self.pool.post_init(recompute, new_field)
    #             # _logger.error("queue %s", self.pool._post_init_queue)
    #             # try:
    #             #     recs._recompute_todo(new_field_name)
    #             # except TypeError:
    #             #     return
    #             # self.modified()
    #             # context test to get all records
    #             # recs = self.sudo().search([])
    #             # recs.modified([new_field_name])
    #             # for rec in recs:
    #             #     new_field.determine_value(rec)

    #             # def recompute(field):
    #             #      _logger.error("Storing computed values of %s", field)
    #             #      recs = self.with_context(active_test=False).search([])
    #             #      recs._recompute_todo(field)
    #             # self.pool.post_init(recompute, new_field)

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
        field_name = 'name'
        lang = 'es_MX'
        if self._name != 'product.template':
            return
        def get_compute(field_name, new_field_name, lang):
            @api.depends(field_name)
            def compute(self):
                recs_lang = dict((r['id'], r['name']) for r in self.with_context(lang=lang).read(['id', 'name']))
                for rec in self:
                    rec[new_field_name] = recs_lang[rec.id]
            return compute

        def add(name, field):
            """ add ``field`` with the given ``name`` if it does not exist yet """
            if name not in self._fields:
                self._add_field(name, field)
        def config_strip(key):
            return list(set(map(lambda a: a.strip(' "\''), (tools.config.get(key) or '').split(','))))
        field_type = {'char': fields.Char, 'text': fields.Text}
        translate_models = config_strip('translate_models')
        if self._name not in translate_models:
            return
        translate_models_langs = config_strip('translate_models_langs')
        domain = [('code', 'in', translate_models_langs), ('active', '=', True)]
        for lang in self.env['res.lang'].search(domain).mapped('code'):
            # TODO: Check if not exists the field
            # TODO: Check if the field is indexed?
            for field_name, field in list(self._fields.items()):
                if not field.translate:
                    continue
                try:
                    field_type_class = field_type[field.type]
                except IndexError:
                    continue
                if field_name != 'name':
                    continue
                new_field_name = "%s_%s" % (field_name, lang.lower())
                new_method_name = "_compute_%s" % new_field_name
                new_field = fields.Char(
                    compute=get_compute(field_name, new_field_name, lang),
                    store=True, index=True, prefetch=False)
                # new_field = fields.Char(compute=get_compute(field_name, new_field_name, lang), store=True, index=True)
                add(new_field_name, new_field)

    # TODO: patch read metho
    # TODO: patch _order_by method
    # TODO: patch _search
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # env['product.template'].with_context(lang='es_MX', prefetch_fields=False).search([('name', 'ilike', 'alojamien')])
        lang = 'es_MX'
        field = 'name'
        model = 'product.template'
        # TODO: Check if the field is defined
        # TODO: Change "product_template"."name_es_mx" as "name_es_mx" ->
        #               "product_template"."name_es_mx" as "name" ->
        # TODO: Support "product_id.name" domains
        if self._name == model and self.env.context.get('lang') == lang:
            new_field = "%s_%s" % (field, lang.lower())
            new_args = []
            for arg in args:
                if isinstance(arg, tuple) and len(arg) == 3 and arg[0] == field:
                    # new_args.append((arg[0].replace(field, new_field),) + arg[1:])
                    new_args.append((new_field,) + arg[1:])
                else:
                    new_args.append(arg)
        else:
            new_args = args
        return super()._search(new_args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

    @api.model
    def _generate_translated_field(self, table_alias, field, query):
        lang = 'es_MX'
        old_field = 'name'
        model = 'product.template'
        new_field = "%s_%s" % (field, lang.lower())
        if self._name == model and self.env.lang == lang and field == old_field:
            return '"%s"."%s"' % (table_alias, new_field)
        return super()._generate_translated_field(table_alias, field, query)


    @api.model
    def _generate_order_by(self, order_spec, query):
        res = []
        lang = 'es_MX'
        field = 'name'
        new_field = '%s_%s' % (field, lang.lower())
        # import pdb;pdb.set_trace()
        # TODO: Check bypass patch of order
        order_spec = order_spec or self._order
        for order_part in order_spec and order_spec.split(',') or []:
            order_split = order_part.strip().split(' ')
            order_field = order_split[0].strip()
            if order_field == field:
                if self.env.context.get('lang') == lang:
                    order_part = order_part.replace('name', new_field)
            res.append(order_part)
        order_spec = ','.join(res)
        return super()._generate_order_by(order_spec, query)

    # este es el causo que fallara con recursion
    # @api.multi
    # def _read_from_database(self, field_names, inherited_field_names=[]):
    #     model = 'product.template'
    #     lang = 'es_MX'
    #     old_field = 'name'
    #     new_field = "%s_%s" % (old_field, lang.lower())
    #     if self._name == model and self.env.context.get('lang') == lang:
    #         new_field_names = []
    #         for field_name in field_names:
    #             if field_name == old_field:
    #                 field_name = new_field
    #                 # self._fields[new_field].name = old_field
    #                 # TODO: Revert original value at final
    #             new_field_names.append(field_name)
    #     else:
    #         new_field_names = field_names
    #     return super()._read_from_database(new_field_names, inherited_field_names=inherited_field_names)


    @api.model
    def _setup_base(self):
        res = super()._setup_base()
        self._add_magic_translated_fields()
        # cls._proper_fields = set(cls._fields)
        # self._add_inherited_fields()
        # cls.pool.model_cache[cls.__bases__] = cls
        return res


    # def _register_hook(self):

    # # def __new__(cls):
    # #     cls.new_field_name = fields.Char()
    # #     _logger.warning("borrar")
    # #     return super(Base, cls).__new__()

    # @api.model
    # def _add_magic_translated_fields(self):
    #     """Add translation field indexed for models defined in the configuration file
    #         e.g. translate_models = product.template,res.partner
    #              translate_models_langs = es_MX
    #     """
    #     # TODO: Update the field if the term is translated directly
    #     # TODO: Delete indexes and columns if they are deleted in configuration file
    #     # ALTER TABLE product_template DROP COLUMN name_en_us;
    #     # ALTER TABLE product_template DROP COLUMN description_en_us;
    #     # ALTER TABLE product_template DROP COLUMN description_purchase_en_us;
    #     # ALTER TABLE product_template DROP COLUMN description_sale_en_us;
    #     # try:
    #     #     self._auto_init()
    #     # except exceptions.UserError:
    #     #     return
    #     def add(name, field):
    #         """ add ``field`` with the given ``name`` if it does not exist yet """
    #         if name not in self._fields:
    #             self._add_field(name, field)
    #     def config_strip(key):
    #         return list(set(map(lambda a: a.strip(' "\''), (tools.config.get(key) or '').split(','))))
    #     field_type = {'char': fields.Char, 'text': fields.Text}
    #     translate_models = config_strip('translate_models')
    #     if self._name not in translate_models:
    #         return
    #     translate_models_langs = config_strip('translate_models_langs')
    #     domain = [('code', 'in', translate_models_langs), ('active', '=', True)]
    #     for lang in self.env['res.lang'].search(domain).mapped('code'):
    #         # TODO: Check if not exists the field
    #         # TODO: Check if the field is indexed?
    #         for field_name, field in list(self._fields.items()):
    #             if not field.translate:
    #                 continue
    #             try:
    #                 field_type_class = field_type[field.type]
    #             except IndexError:
    #                 continue
    #             if field_name != 'name':
    #                 continue
    #             new_field_name = "%s_%s" % (field_name, lang.lower())
    #             new_method_name = "_compute_%s" % new_field_name
    #             # _logger.warning("field_name %s", field_name)
    #             def _get_method(field_name, new_field_name, lang):
    #                 @api.depends(field_name)
    #                 def _compute_translated_field(self):
    #                     # _logger.info("Computing %s based on %s with lang %s", new_field_name, field_name, lang)
    #                     # import pdb;pdb.set_trace()
    #                     for rec in self.with_context(lang=lang):
    #                         # _logger.info("record %s values of %s:'%s' stored in %s", rec, field_name, rec[field_name], new_field_name)
    #                         rec[new_field_name] = rec[field_name]
    #                         # _logger.info("Rec %s Value stored in %s: %s", rec, new_field_name, getattr(rec, new_field_name, False))
    #                         # rec.write({new_field_name: rec[field_name]})
    #                         rec.update({new_field_name: rec[field_name]})
    #                         setattr(rec, new_field_name, rec[field_name])
    #                 return _compute_translated_field

    #             cls = type(self)
    #             # _logger.warning("new method %s for %s lang %s", new_method_name, new_field_name, lang)
    #             new_method = _get_method(field_name, new_field_name, lang)
    #             setattr(cls, new_method_name, new_method)
    #             # setattr(cls, new_method_name, _get_method(field_name, new_field_name, lang))
    #             # self._patch_method(new_method_name, _get_method(field_name, new_field_name, lang))
    #             new_field = field_type_class(automatic=True, index=True, store=True, readonly=True,
    #                                          # compute=getattr(cls, new_method_name))
    #                                          compute=new_method_name)
    #             # new_field.setup_triggers(self._name)
    #             add(new_field_name, new_field)
    #             # self.setup_triggers(self._name)
    #             # _logger.info("New field added %s.%s", self._name, new_field_name)
    #             # recs = self.with_context(active_test=False).search([])
    #             # _logger.info("Re-computing field added %s.%s", self._name, new_field_name)
    #             # def recompute_method(self):
    #             # def recompute(field):
    #             #     _logger.error("Storing computed values of %s", field)
    #             #     recs = self.with_context(active_test=False).search([])
    #             #     recs._recompute_todo(field)
    #             #     # return recompute
    #             # _logger.error("aqui")
    #             # _logger.error("ANTES queue %s", self.pool._post_init_queue)
    #             # self.pool.post_init(recompute, new_field)
    #             # _logger.error("queue %s", self.pool._post_init_queue)
    #             # try:
    #             #     recs._recompute_todo(new_field_name)
    #             # except TypeError:
    #             #     return
    #             # self.modified()
    #             # context test to get all records
    #             # recs = self.sudo().search([])
    #             # recs.modified([new_field_name])
    #             # for rec in recs:
    #             #     new_field.determine_value(rec)

    #             def recompute(field):
    #                  _logger.error("Storing computed values of %s", field)
    #                  recs = self.with_context(active_test=False).search([])
    #                  recs._recompute_todo(field)
    #             self.pool.post_init(recompute, new_field)


    # @api.model
    # def _setup_base(self):
    #     self._add_magic_translated_fields()
    #     return super(Base, self)._setup_base()
    # # @api.model
    # # def _add_magic_fields(self):
    # #     self._add_magic_translated_fields()
    # #     return super(Base, self)._add_magic_fields()

    # # def _register_hook(self):
    # #     self._add_magic_translated_fields()
    # #     self._unregister_hook()
    # #     # self._register_hook()
    # #     return super()._register_hook()

    # # def __init__(self, *args, **kwargs):
    # #     super(Base, self).__init__(*args, **kwargs)
    # #     new_field_name = fields.Char()
    # #     import pdb;pdb.set_trace()
    # #     print(self._fields)
    # #     self._fields['new_field_name'] = self.new_field_name

    # # @api.model_cr
    # # def _register_hook(self):
    # #     """Register marked jobs"""
    # #     super(Base, self)._register_hook()
    # #     self.new_field_name = fields.Char()
    # #     _logger.warning("borrar")
