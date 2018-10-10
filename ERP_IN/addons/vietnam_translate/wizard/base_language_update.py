from odoo import api, fields, models, _, tools
from odoo.modules import get_module_path
import os
import logging
_logger = logging.getLogger(__name__)

class base_language_update(models.TransientModel):
    _name = "base.language.update"

    module_upgrade = fields.Many2many('ir.module.module', string='Module Upgrade')

    def get_path_module_translate(self):
        path_modules = get_module_path('vietnam_translate')
        # if path_modules:
        #     path_modules = os.path.join(path_modules, 'i18n')
        #     list_path_module = []
        #     files = os.listdir(path_modules)
        #     if files:
        #         for f in files:
        #             path_module = os.path.join(path_modules, f)
        #             list_path_module.append(path_module)
        # return list_path_module
        list_path_module = []
        # print path_modules
        if path_modules and not self.module_upgrade:
            path_modules = os.path.join(path_modules, 'i18n')
            files = os.listdir(path_modules)
            if files:
                for f in files:
                    path_module = os.path.join(path_modules, f)
                    list_path_module.append(path_module)
        if self.module_upgrade:
            path_modules = os.path.join(path_modules, 'i18n')
            files = os.listdir(path_modules)
            for module in self.module_upgrade:
                exist_module = list(filter(lambda x: x == (module.name + '.po'), files))
                if exist_module:
                    path_module = os.path.join(path_modules, exist_module[0])
                    list_path_module.append(path_module)
                else:
                    module_dir = get_module_path(module.name)
                    module_dir = os.path.join(module_dir, 'i18n')
                    files_dir = os.listdir(module_dir)
                    module_directory = os.path.join(module_dir, files_dir[0])
                    list_path_module.append(module_directory)
        return list_path_module

    def update_language(self):
        context = dict(self._context)
        context['overwrite'] = True
        path_modules_list = self.get_path_module_translate()
        module_name_list = []
        module_name_dict = {}
        if path_modules_list:
            if not self.module_upgrade:
                for path_module in path_modules_list:
                    path, file = os.path.split(path_module)
                    module_name = file.replace('.po', '')
                    module_name_list.append(module_name)
                    module_name_dict[module_name] = path_module
                    # modules = self.env['ir.module.module'].sudo().search(
                    #     [
                    #         ('name', '=', module_name),
                    #         ('state', 'in', ['installed', 'to upgrade', 'to remove'])
                    #     ])

                modules = self.env['ir.module.module'].sudo().search_read(
                    [
                        ('name', 'in', module_name_list),
                        ('state', 'in',
                         ['installed', 'to upgrade', 'to remove'])
                    ], ['name'])
                if modules:
                    self.env.cr.execute(
                        "delete from ir_translation where module in %s",
                        (tuple(module_name_list),))

                for module in modules:
                    path_module = module_name_dict.get(module['name'])
                    tools.trans_load(self._cr, path_module, 'vi_VN', verbose=False, module_name=module['name'], context=context)
            else:
                for path_module in self.module_upgrade:
                    # path, file = os.path.split(path_module)
                    # module_name = file.replace('.po', '')
                    module_name_list.append(path_module.name)
                    module_name_dict[path_module.name] = path_module

                modules = self.env['ir.module.module'].sudo().search_read(
                    [
                        ('name', 'in', module_name_list),
                        ('state', 'in',
                         ['installed', 'to upgrade', 'to remove'])
                    ], ['name'])
                if modules:
                    self.env.cr.execute(
                        "delete from ir_translation where module in %s",
                        (tuple(module_name_list),))

                for module in modules:
                    path_vn = get_module_path('vietnam_translate')
                    path_modules = os.path.join(path_vn, 'i18n')
                    files_list = os.listdir(path_modules)
                    exist_module = list(filter(lambda x: x == (module['name'] + '.po'), files_list))
                    if exist_module:
                        # path_module = module_name_dict.get(module['name'])
                        tools.trans_load(self._cr, (path_modules+'\\'+exist_module[0]), 'vi_VN', verbose=False, module_name=module['name'],
                                         context=context)
                    else:
                        module_dir = get_module_path(module['name'])
                        module_dir = os.path.join(module_dir, 'i18n')
                        files_dir = os.listdir(module_dir)
                        module_directory = os.path.join(module_dir, files_dir[0])
                        tools.trans_load(self._cr, module_directory, 'vi_VN', verbose=False, module_name=module['name'],
                                         context=context)
        return {'type': 'ir.actions.act_window_close'}

