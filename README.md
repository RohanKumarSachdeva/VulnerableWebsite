# VulnerableWebsite
* Student management website which is prone to OWASP vulnerabilities

## How to run
* Prerequisite: Install Docker Desktop
* Clone this repository `https://github.com/RohanKumarSachdeva/VulnerableWebsite`
* Change the directory to `VulnerableWebsite`
* Run `docker-compose up`
* Browse to `http://127.0.0.1:5000/` to access the application

## OWASP vulnerabilities Detail and their Remediations
### 1. SQL Injection:
#### Attack Details:
This vulnerability allows an attacker to interfere with the queries that an application makes to its database by
**subverting the query logic**.
Our vulnerable application lets users log in with a username and password. If a user submits the username `adam` and the password `qwerty`, the application checks the credentials by concatenating them shown below, and forms a SQL query:
> "SELECT * FROM accounts WHERE username=" + username + " AND password=" + password

Which transforms to:
> SELECT * FROM users WHERE username = 'adam' AND password = 'qwerty'

If the query returns the details of a user, then the login is successful. Otherwise, it is rejected.

Here, an attacker can log in as any user without a password simply by using the SQL comment sequence `-- ` which will comment out the password check from the `WHERE` clause of the query. For example, submitting the username **`admin'-- `** and a blank/wrong password results in the following query:
> SELECT * FROM users WHERE username = 'admin'--' AND password = ''

This query returns the user **in-band** if its username `admin` exists in the database and successfully logs the attacker in as that user.

#### Remediation Steps: Following are the best practices to avoid SQL Injection
* **Using Prepared/Parameterized statements**. These are pre-compiled SQL statements. The query is already pre-compiled, so the final query will not go through the compilation phase again. For this reason, the user-provided data will always be interpreted as a simple string and cannot modify the original query’s logic. Hence to fix the vulnerability in our application we can use the following parameterized statement where `%s` are placeholders used for parameters that will be supplied during execution time.
> 'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password)

* **Escaping of user data**. If a parameterized API is not available, you should carefully escape special characters using the specific escape syntax for that interpreter. Escaping involves adding a special character before the character/string to avoid it being misinterpreted, for example, adding a `\` character before a `"(double quote)` character so that it is interpreted as text and not as closing a string.

* **HtmlEncode all user input.** Encoding (commonly called “Output Encoding”) involves translating special characters into some different but equivalent form that is no longer dangerous in the target interpreter, for example translating the `<` character into the `&lt`.