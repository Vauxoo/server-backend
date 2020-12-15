import itertools
import logging

from odoo import api, fields, models, tools

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
        # TODO: Delete indexes and columns if they are deleted in configuration file
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
        for lang in self.env['res.lang'].search([('code', 'in', translate_models_langs)]).mapped('code'):
            # import pdb;pdb.set_trace()
            # TODO: Check if not exists the field
            # TODO: Check if the field is char or text
            for field_name, field in list(self._fields.items()):
                if not field.translate:
                    continue
                try:
                    field_type_class = field_type[field.type]
                except IndexError:
                    continue
                new_field_name = "%s_%s" % (field_name, lang.lower())
                new_method = "_compute_%s" % new_field_name

                @api.depends(field_name)
                def _compute_translated_field(self):
                    _logger.info("Computing %s based on %s with lang %s", new_field_name, field_name, lang)
                    for rec in self.with_context(lang=lang):
                        _logger.info("record %s values %s stored in %s", rec, rec[field_name], new_field_name)
                        rec[new_field_name] = rec[field_name]

                cls = type(self)
                setattr(cls, new_method, _compute_translated_field)
                new_field = field_type_class(automatic=True, index=True, store=True, readonly=True,
                                             compute=new_method)
                add(new_field_name, new_field)
                _logger.info("New field added %s.%s", self._name, new_field_name)

    @api.model
    def _add_magic_fields(self):
        self._add_magic_translated_fields()
        return super(Base, self)._add_magic_fields()

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
