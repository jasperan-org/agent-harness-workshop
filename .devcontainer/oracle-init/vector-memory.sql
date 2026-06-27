-- Size Oracle's Vector Memory Pool so in-memory HNSW indexes can build.
-- On the Free image VECTOR_MEMORY_SIZE defaults to 0 → HNSW fails with ORA-51962.
-- 256M is ample for this workshop's data and — crucially — stays well within the
-- Free edition's SGA budget. (Oversizing it, e.g. 1024M, starves the shared pool
-- and triggers ORA-04031, which makes every query crawl. 256M is the safe number.)
-- gvenzl/oracle-free runs files in /container-entrypoint-startdb.d/ as SYSDBA on
-- every container start, so this re-applies automatically.
WHENEVER SQLERROR CONTINUE
ALTER SYSTEM SET VECTOR_MEMORY_SIZE = 256M SCOPE=BOTH;
ALTER SESSION SET CONTAINER = FREEPDB1;
ALTER SYSTEM SET VECTOR_MEMORY_SIZE = 256M SCOPE=BOTH;
EXIT;
