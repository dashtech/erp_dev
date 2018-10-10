# -*- coding: utf-8 -*-
import datetime
from odoo import http

class MainUpdate(http.Controller):
    @http.route(
        '/update-message-to-mobile-state/<string:callback_token>/<int:res_id>/<string:client_type>/<int:client_id>',
        type='http',
        auth='public',
        website=True,
        csrf=False)
    def main_update(self, callback_token, res_id, client_type, client_id, **kw):
        # check field (user_id/partner_id)
        update_field_dict = {'u': 'user_id',
                             'p': 'partner_id'}

        update_field_name = update_field_dict.get(client_type, False)
        if not update_field_name:
            return 'Client type invalid'

        # update field (user_ids, partner_ids)
        check_field_dict = {'u': 'user_ids',
                            'p': 'partner_ids'}

        check_field_name = check_field_dict.get(client_type, False)
        if not check_field_name:
            return 'Client type invalid'

        # find message to update
        callback_token = '{}/{}'.format(callback_token, res_id)
        domain = [('state', '=', 'sending'),
                  ('callback_token', '=', callback_token),
                  ('id', '=', res_id)]

        messages = http.request.env['notify.message'].sudo().search(domain)

        if not messages:
            return 'Message not found'

        # check client_id to update in client to send of message
        check_ids = getattr(messages[0], check_field_name)._ids
        if client_id not in check_ids:
            return 'Client not in clients of message'

        # check client_id to update updated ?
        domain = [('message_id', '=', messages[0].id),
                  (update_field_name, '=', client_id),
                  ]
        duplicate_result = \
            http.request.env['notify.message.result'
            ].sudo().search(domain)

        if duplicate_result:
            return 'Client updated'

        result = kw.get('result', False)
        state_dict = {'1': 'success',
                      '0': 'fail'}
        state = state_dict.get(result, False)
        if not state:
            return 'Result invalid'

        reason = kw.get('reason', '')
        time = kw.get('time', False)

        messages[0].write(
            {'result_ids': [(0, 0, {update_field_name: client_id,
                                    'state': state,
                                    'reason': reason})]}
        )

        return 'OK'
