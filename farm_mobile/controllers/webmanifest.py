from odoo.addons.web.controllers.webmanifest import WebManifest
from odoo.http import request

class FarmWebManifest(WebManifest):

    def _get_service_worker_content(self):
        """ 
        By inheriting the native controller, append custom logic to the Service Worker [US-007-06]
        This reuses the Odoo 18 PWA framework while adding the business extension.
        """
        body = super()._get_service_worker_content()
        
        # Append background-sync and custom caching logic
        custom_logic = """
// --- Farm Mobile Custom Logic ---
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-field-evidence') {
    event.waitUntil(syncEvidenceData());
  }
});

async function syncEvidenceData() {
  console.log('PWA: Syncing offline evidence data...');
  / IndexedDB data and upload it
}
"""
        return body + custom_logic