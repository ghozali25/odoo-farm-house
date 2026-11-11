from . import models
from . import wizard  # 18.0 port (koordinator, saat install): wizard/ tidak pernah
# di-import upstream (19.0 juga) sehingga model TransientModel
# 'livestock.death.report' tidak pernah ter-register; CSV akses yang
# ditambahkan pekerja porting merujuk model_id itu dan install gagal
# ("No matching record found for external id 'model_livestock_death_report'").
# Dengan import ini model ter-register dan aturan aksesnya valid.
