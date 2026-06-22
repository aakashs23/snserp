-- Enable RLS on all tables
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_ai ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;

-- Allow read access for authenticated users to public tables
CREATE POLICY "Allow read access to authenticated users" ON roles FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read access to authenticated users" ON permissions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read access to authenticated users" ON role_permissions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read access to authenticated users" ON users FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read access to authenticated users" ON customers FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow read access to authenticated users" ON invoices FOR SELECT TO authenticated USING (true);

-- Allow all operations for Service Role (used by FastAPI backend)
-- The service role bypasses RLS anyway if using the service key, but it's good practice.

-- Create a trigger function to automatically insert into public.users when a user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
  default_role_id uuid;
BEGIN
  -- Attempt to get a default role like 'viewer' or 'admin' depending on logic.
  -- For now, if no roles exist, we insert an 'admin' role and assign it.
  SELECT id INTO default_role_id FROM public.roles WHERE name = 'admin' LIMIT 1;
  
  IF default_role_id IS NULL THEN
    -- Fallback: create the admin role
    INSERT INTO public.roles (id, name, description) VALUES (gen_random_uuid(), 'admin', 'System Administrator') RETURNING id INTO default_role_id;
  END IF;

  INSERT INTO public.users (id, full_name, email, role_id)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'full_name', new.email),
    new.email,
    default_role_id
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger the function every time a user is created
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
