# NOTE (18.0 port): this file used to re-define stock.lot fields that are
# already defined in models/farm_trait.py (father_id, mother_id,
# trait_value_ids, trait_score_avg) -- with a CONFLICTING type for
# trait_score_avg: Selection here vs. computed Float there. Whichever
# definition won at registry build time broke the other side (the Float
# compute cannot write into a Selection field, and the priority widget in
# views/breeding_views.xml cannot render a Float). All four fields now live
# only in farm_trait.py; this module is kept as a documented placeholder so
# the import in models/__init__.py stays valid.
