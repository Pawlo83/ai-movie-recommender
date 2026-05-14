


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_cron" WITH SCHEMA "pg_catalog";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."get_all_tables"() RETURNS TABLE("table_name" "text")
    LANGUAGE "sql" STABLE
    AS $$
    select tablename
    from pg_tables
    where schemaname = 'public'
    order by tablename;
$$;


ALTER FUNCTION "public"."get_all_tables"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_random_films"() RETURNS TABLE("name" "text", "release_date" "date", "tmdb_id" "text")
    LANGUAGE "sql"
    AS $$SELECT
    name,
    release_date,
    tmdb_id
  FROM films
  WHERE is_valid=True
  ORDER BY random()
  LIMIT 10;$$;


ALTER FUNCTION "public"."get_random_films"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_tag_usage"() RETURNS TABLE("tag_name" "text", "uses" bigint)
    LANGUAGE "plpgsql" STABLE
    AS $$
begin
    return query
      SELECT
             t.tag_name AS tag_name,
             COUNT(ft.film_id) AS uses
      FROM films_tags ft
      JOIN tags t ON ft.tag_id = t.id
      GROUP BY t.id, t.tag_name
      ORDER BY uses DESC;
end;
$$;


ALTER FUNCTION "public"."get_tag_usage"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."mark_old_gpt_responses_as_invalid"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$BEGIN
  UPDATE gpt_response
  SET is_valid = FALSE
  WHERE updated_at < (now() - interval '14 days')
  AND is_valid = TRUE;
END;$$;


ALTER FUNCTION "public"."mark_old_gpt_responses_as_invalid"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;$$;


ALTER FUNCTION "public"."update_updated_at"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."films" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "name" "text",
    "release_date" "date",
    "director" "text",
    "tmdb_id" "text",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "is_valid" boolean
);


ALTER TABLE "public"."films" OWNER TO "postgres";


COMMENT ON TABLE "public"."films" IS 'Table for films';



CREATE TABLE IF NOT EXISTS "public"."films_tags" (
    "film_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "tag_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."films_tags" OWNER TO "postgres";


COMMENT ON TABLE "public"."films_tags" IS 'Table use for many to many relation';



CREATE OR REPLACE VIEW "public"."films_tags_view" WITH ("security_invoker"='on') AS
 SELECT "film_id",
    "tag_id",
    "created_at",
    "updated_at"
   FROM "public"."films_tags";


ALTER VIEW "public"."films_tags_view" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."films_view" WITH ("security_invoker"='on') AS
 SELECT "id",
    "name",
    "director",
    "release_date",
    "tmdb_id",
    "is_valid",
    "created_at",
    "updated_at"
   FROM "public"."films";


ALTER VIEW "public"."films_view" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."gpt_response" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "request" "jsonb",
    "response" "jsonb",
    "is_valid" boolean,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "description" "text"
);


ALTER TABLE "public"."gpt_response" OWNER TO "postgres";


COMMENT ON TABLE "public"."gpt_response" IS 'Responses from LLM in order to improve performance';



CREATE OR REPLACE VIEW "public"."gpt_response_view" WITH ("security_invoker"='on') AS
 SELECT "id",
    "request",
    "description",
    "response",
    "is_valid",
    "created_at",
    "updated_at"
   FROM "public"."gpt_response";


ALTER VIEW "public"."gpt_response_view" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tags" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "tag_name" "text",
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."tags" OWNER TO "postgres";


COMMENT ON TABLE "public"."tags" IS 'Table used for tags';



CREATE OR REPLACE VIEW "public"."tags_view" WITH ("security_invoker"='on') AS
 SELECT "id",
    "tag_name",
    "created_at",
    "updated_at"
   FROM "public"."tags";


ALTER VIEW "public"."tags_view" OWNER TO "postgres";


ALTER TABLE ONLY "public"."films"
    ADD CONSTRAINT "films_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."films_tags"
    ADD CONSTRAINT "films_tags_pkey" PRIMARY KEY ("film_id", "tag_id");



ALTER TABLE ONLY "public"."gpt_response"
    ADD CONSTRAINT "gpt_response_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."tags"
    ADD CONSTRAINT "tags_pkey" PRIMARY KEY ("id");



CREATE OR REPLACE TRIGGER "films_tags_updated_at" BEFORE UPDATE ON "public"."films_tags" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "films_updated_at" BEFORE UPDATE ON "public"."films" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "gpt_response_updated_at" BEFORE UPDATE ON "public"."gpt_response" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



CREATE OR REPLACE TRIGGER "tags_updated_at" BEFORE UPDATE ON "public"."tags" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at"();



ALTER TABLE ONLY "public"."films_tags"
    ADD CONSTRAINT "films_tags_film_id_fkey" FOREIGN KEY ("film_id") REFERENCES "public"."films"("id");



ALTER TABLE ONLY "public"."films_tags"
    ADD CONSTRAINT "films_tags_tag_id_fkey" FOREIGN KEY ("tag_id") REFERENCES "public"."tags"("id");



ALTER TABLE "public"."films" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."films_tags" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."gpt_response" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."tags" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";














































































































































































GRANT ALL ON FUNCTION "public"."get_all_tables"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_all_tables"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_all_tables"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_random_films"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_random_films"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_random_films"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_tag_usage"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_tag_usage"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_tag_usage"() TO "service_role";



GRANT ALL ON FUNCTION "public"."mark_old_gpt_responses_as_invalid"() TO "anon";
GRANT ALL ON FUNCTION "public"."mark_old_gpt_responses_as_invalid"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."mark_old_gpt_responses_as_invalid"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at"() TO "service_role";
























GRANT ALL ON TABLE "public"."films" TO "anon";
GRANT ALL ON TABLE "public"."films" TO "authenticated";
GRANT ALL ON TABLE "public"."films" TO "service_role";



GRANT ALL ON TABLE "public"."films_tags" TO "anon";
GRANT ALL ON TABLE "public"."films_tags" TO "authenticated";
GRANT ALL ON TABLE "public"."films_tags" TO "service_role";



GRANT ALL ON TABLE "public"."films_tags_view" TO "anon";
GRANT ALL ON TABLE "public"."films_tags_view" TO "authenticated";
GRANT ALL ON TABLE "public"."films_tags_view" TO "service_role";



GRANT ALL ON TABLE "public"."films_view" TO "anon";
GRANT ALL ON TABLE "public"."films_view" TO "authenticated";
GRANT ALL ON TABLE "public"."films_view" TO "service_role";



GRANT ALL ON TABLE "public"."gpt_response" TO "anon";
GRANT ALL ON TABLE "public"."gpt_response" TO "authenticated";
GRANT ALL ON TABLE "public"."gpt_response" TO "service_role";



GRANT ALL ON TABLE "public"."gpt_response_view" TO "anon";
GRANT ALL ON TABLE "public"."gpt_response_view" TO "authenticated";
GRANT ALL ON TABLE "public"."gpt_response_view" TO "service_role";



GRANT ALL ON TABLE "public"."tags" TO "anon";
GRANT ALL ON TABLE "public"."tags" TO "authenticated";
GRANT ALL ON TABLE "public"."tags" TO "service_role";



GRANT ALL ON TABLE "public"."tags_view" TO "anon";
GRANT ALL ON TABLE "public"."tags_view" TO "authenticated";
GRANT ALL ON TABLE "public"."tags_view" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































