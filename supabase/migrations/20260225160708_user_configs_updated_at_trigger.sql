-- 1. Ensure the extension exists in the extensions schema
CREATE EXTENSION IF NOT EXISTS moddatetime SCHEMA extensions;

-- 2. Safely drop the trigger if you accidentally created a broken version
DROP TRIGGER IF EXISTS handle_updated_at ON user_configs;

-- 3. Create the trigger with the explicit schema path
CREATE TRIGGER handle_updated_at 
  BEFORE UPDATE ON user_configs
  FOR EACH ROW 
  EXECUTE FUNCTION extensions.moddatetime(updated_at);
