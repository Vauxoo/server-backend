# Copyright 2022 - JarsaP (http://www.jarsa.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

records_to_remove = [
    "base_user_role.view_res_users_role_form",
    "base_user_role.view_res_users_form_inherit",
    "base_user_role.view_res_users_search_inherit"
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.delete_records_safely_by_xml_id(env, records_to_remove)
    _logger.info("View for base_user_role deleted.")
