Add to your odoo configuraion file (by default ~/.odoorc)
the following ``[options]``

 * translate_models: All models _name to enable this feature (e.g. "product.template,res.partner")
 * translate_models_langs: All language to enable this feature in ISO code (e.g. "es_MX,en_US")
 * translate_fields_{model_name_replace_dots2underscore}: All fields to enable in this model. Empty for all fields (e.g. "name,description_sale")

Example

.. code-block::
    translate_models = website,product.template,res.partner
    translate_models_langs = es_MX,en_US
    # translate_fields_product_template =  # All them
    translate_fields_res_partner = website_meta_description,website_short_description,website_meta_keywords,website_meta_title

After enable this parameters is required to update the module where the model was defined

.. code-block::
    odoo-bin ... --update product,website,base

Check the new fields created and now they will be used.
