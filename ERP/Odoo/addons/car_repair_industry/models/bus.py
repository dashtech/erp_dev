from odoo.addons.bus.controllers.main import BusController
from odoo.http import request


class BBusController(BusController):
    # --------------------------
    # Extends BUS Controller Poll
    # --------------------------
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            channels = list(channels)
            channels.append((request.db, 'btek.notify', request.env.user.partner_id.id))
        return super(BBusController, self)._poll(dbname, channels, last, options)


BBusController()
