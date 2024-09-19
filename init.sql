ALTER USER 'root' IDENTIFIED WITH 'caching_sha2_password' BY '123456789';
FLUSH PRIVILEGES;
SELECT 'User Authentication Plugin Modified Successfully' AS message;