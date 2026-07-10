-- Close the two access-control tables that were never covered by 0000_rls_policies.sql.
--
-- Verified against the live database before writing this: with nothing but the
-- public anon key (which ships to every browser), this returned real rows —
-- every user's document ACL — straight out of PostgREST, bypassing FastAPI:
--
--     curl "$SUPABASE_URL/rest/v1/document_permissions?select=*" \
--          -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY"
--     => 200 [{"document_id":"...","user_id":"...", ...}]
--
-- document_shares has the same exposure; it only returned [] because it is
-- currently empty. Both are association tables created by SQLAlchemy models
-- (app/models/document_permissions.py, the document_shares table in
-- app/models/documents.py) and neither appears in 0000_rls_policies.sql.
--
-- No CREATE POLICY here, deliberately. In Postgres, "RLS enabled + zero
-- policies" is default-deny for anon/authenticated, which is exactly what the
-- other 12 tables in 0000_rls_policies.sql already rely on. Adding permissive
-- policies would only create a chance to widen access by mistake.
--
-- The FastAPI backend is unaffected: it connects as the table owner over
-- asyncpg and with the Supabase service_role key, both of which bypass RLS.
-- The frontend never queries these tables directly (it holds no `.from()`
-- calls at all — every read goes through the backend).

ALTER TABLE document_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_shares ENABLE ROW LEVEL SECURITY;
