Desktop приложение для полкючение к бд и выполнение запрососв. Результат  запроса отображется в виде таблицы.
Возможно подключиться к следующим БД:
* Postgres
* sqlite 
* mysql

#### sqlite

Если файл бд не существует, то он создается.

Пример для connection string:
* `sqlite://:memmory:` или `sqlite://` - подключение в память
* `sqlite://dbname.sqlite` - подключение к файлу в локальной папке.  
* `sqlite:////path/to/dbname.sqlite` - подключение к файлу по абсолютному пути.

#### postgres

Для подключение нужно установаить psycopg2.  
```bash
        pip install psycopg2
```
Пример для connection string:
* `postgresql://user:pasword@hostname:port/dbname`

#### mysql

Для подключение нужно установаить pymysql.  
```bash
        pip install pymysql
```
Пример для connection string:
* `mysql://user:pasword@hostname:port/dbname`
 

