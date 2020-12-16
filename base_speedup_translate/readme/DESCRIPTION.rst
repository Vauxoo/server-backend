This module improves retrieving products when a language is installed and configured.
The default behaviour is to get translated the columns of products, website, partners and so on.
which in this case would be slow
because Odoo will process the product's name to translate it.

Warning: This module adds new columns to original model for each lang enabled
it could increase a lot the size of your database

Odoo to get translated(column) uses the following way:

.. code-block::

    SELECT "product_product".id
    FROM   "product_product"
    LEFT JOIN "product_template" AS "product_product__product_tmpl_id"
        ON ( "product_product"."product_tmpl_id" =
            "product_product__product_tmpl_id"."id" )
    LEFT JOIN (SELECT res_id,
                        value
                FROM   "ir_translation"
                WHERE  type = 'model'
                        AND name = 'product.template,name'
                        AND lang = 'es_MX'
                        AND value != '') AS
                "product_product__product_tmpl_id__name"
        ON ( "product_product__product_tmpl_id"."id" =
                        "product_product__product_tmpl_id__name"."res_id" )
    WHERE  ( "product_product"."active" = true )
    ORDER  BY "product_product"."default_code",
            Coalesce("product_product__product_tmpl_id__name"."value",
            "product_product__product_tmpl_id"."name"),
            "product_product"."id"
    LIMIT  10


Using a production database executing this query the result is:
 - Planning Time: 1.088 ms
 - Execution Time: 1027.282 ms
 - Total Time: 1028.37 ms

It is so slow.

Using this module a new field is created called {field}_{lang}
for example for the lang es_MX the field product_template.name
a new field is created in product_template.name_es_mx
if original field has `index=True` so the new field will have too

It transform the same query to

.. code-block::

    SELECT "product_product".id
    FROM   "product_product"
    WHERE  ( "product_product"."active" = true )
    ORDER  BY "product_product"."name_es_mx"
    LIMIT  10

The new result is:
 - Planning Time: 0.095 ms
 - Execution Time: 0.529 ms
 - Total Time: 0.624 ms

It is 1.65k times faster

It is because the field ``name`` has the parameter ``translate=True``

So, It will process the original value to translate it

Then, It will order by a column computed on-the-fly of other tables

Opening the ``/shop`` page could consume 7.5s instead of 1.2s without this module

More info about this on:

  https://github.com/odoo/odoo/pull/61618
