make:
	docker exec -itu postgres pg_data psql -c 'create database bot_db'

remove:
	docker exec -itu postgres pg_data psql -c 'drop database bot_db'
