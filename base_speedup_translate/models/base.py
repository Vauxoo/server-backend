import itertools
import logging

from functools import wraps

from odoo import api, fields, models, tools, exceptions

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = 'base'

    # def __new__(cls):
    #     cls.new_field_name = fields.Char()
    #     _logger.warning("borrar")
    #     return super(Base, cls).__new__()

    @api.model
    def _add_magic_translated_fields(self):
        """Add translation field indexed for models defined in the configuration file
            e.g. translate_models = product.template,res.partner
                 translate_models_langs = es_MX
        """
        # TODO: Update the field if the term is translated directly
        # TODO: Delete indexes and columns if they are deleted in configuration file
        # ALTER TABLE product_template DROP COLUMN name_en_us;
        # ALTER TABLE product_template DROP COLUMN description_en_us;
        # ALTER TABLE product_template DROP COLUMN description_purchase_en_us;
        # ALTER TABLE product_template DROP COLUMN description_sale_en_us;
        # try:
        #     self._auto_init()
        # except exceptions.UserError:
        #     return
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
                # _logger.warning("field_name %s", field_name)
                def _get_method(field_name, new_field_name, lang):
                    @api.depends(field_name)
                    def _compute_translated_field(self):
                        # _logger.info("Computing %s based on %s with lang %s", new_field_name, field_name, lang)
                        # import pdb;pdb.set_trace()
                        for rec in self.with_context(lang=lang):
                            # _logger.info("record %s values of %s:'%s' stored in %s", rec, field_name, rec[field_name], new_field_name)
                            rec[new_field_name] = rec[field_name]
                            # _logger.info("Rec %s Value stored in %s: %s", rec, new_field_name, getattr(rec, new_field_name, False))
                            # rec.write({new_field_name: rec[field_name]})
                            rec.update({new_field_name: rec[field_name]})
                            setattr(rec, new_field_name, rec[field_name])
                    return _compute_translated_field

                cls = type(self)
                # _logger.warning("new method %s for %s lang %s", new_method_name, new_field_name, lang)
                new_method = _get_method(field_name, new_field_name, lang)
                setattr(cls, new_method_name, new_method)
                # setattr(cls, new_method_name, _get_method(field_name, new_field_name, lang))
                # self._patch_method(new_method_name, _get_method(field_name, new_field_name, lang))
                new_field = field_type_class(automatic=True, index=True, store=True, readonly=True,
                                             # compute=getattr(cls, new_method_name))
                                             compute=new_method_name)
                # new_field.setup_triggers(self._name)
                add(new_field_name, new_field)
                # self.setup_triggers(self._name)
                # _logger.info("New field added %s.%s", self._name, new_field_name)
                # recs = self.with_context(active_test=False).search([])
                # _logger.info("Re-computing field added %s.%s", self._name, new_field_name)
                # def recompute_method(self):
                # def recompute(field):
                #     _logger.error("Storing computed values of %s", field)
                #     recs = self.with_context(active_test=False).search([])
                #     recs._recompute_todo(field)
                #     # return recompute
                # _logger.error("aqui")
                # _logger.error("ANTES queue %s", self.pool._post_init_queue)
                # self.pool.post_init(recompute, new_field)
                # _logger.error("queue %s", self.pool._post_init_queue)
                # try:
                #     recs._recompute_todo(new_field_name)
                # except TypeError:
                #     return
                # self.modified()
                # context test to get all records
                # recs = self.sudo().search([])
                # recs.modified([new_field_name])
                # for rec in recs:
                #     new_field.determine_value(rec)

                def recompute(field):
                     _logger.error("Storing computed values of %s", field)
                     recs = self.with_context(active_test=False).search([])
                     recs._recompute_todo(field)
                self.pool.post_init(recompute, new_field)


    @api.model
    def _setup_base(self):
        self._add_magic_translated_fields()
        return super(Base, self)._setup_base()
    # @api.model
    # def _add_magic_fields(self):
    #     self._add_magic_translated_fields()
    #     return super(Base, self)._add_magic_fields()

    # def _register_hook(self):
    #     self._add_magic_translated_fields()
    #     self._unregister_hook()
    #     # self._register_hook()
    #     return super()._register_hook()

    # def __init__(self, *args, **kwargs):
    #     super(Base, self).__init__(*args, **kwargs)
    #     new_field_name = fields.Char()
    #     import pdb;pdb.set_trace()
    #     print(self._fields)
    #     self._fields['new_field_name'] = self.new_field_name

    # @api.model_cr
    # def _register_hook(self):
    #     """Register marked jobs"""
    #     super(Base, self)._register_hook()
    #     self.new_field_name = fields.Char()
    #     _logger.warning("borrar")
