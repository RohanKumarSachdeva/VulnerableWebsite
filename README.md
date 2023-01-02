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
> SELECT * FROM users WHERE username = 'admin'-- ' AND password = ''

This query returns the user **in-band** if its username `admin` exists in the database and successfully logs the attacker in as that user.

#### Remediation Steps: Following are the best practices to avoid SQL Injection
* **Using Prepared/Parameterized statements**. These are pre-compiled SQL statements. The query is already pre-compiled, so the final query will not go through the compilation phase again. For this reason, the user-provided data will always be interpreted as a simple string and cannot modify the original query’s logic. Hence to fix the vulnerability in our application we can use the following parameterized statement where `%s` are placeholders used for parameters that will be supplied during execution time.
> 'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password)

* **Escaping of user data**. If a parameterized API is not available, you should carefully escape special characters using the specific escape syntax for that interpreter. Escaping involves adding a special character before the character/string to avoid it being misinterpreted, for example, adding a `\` character before a `"(double quote)` character so that it is interpreted as text and not as closing a string.

* **HtmlEncode all user input.** Encoding (commonly called “Output Encoding”) involves translating special characters into some different but equivalent form that is no longer dangerous in the target interpreter, for example translating the `<` character into the `&lt`.


### 2. Stored Cross Site Scripting (XSS): can cause RCE
#### Attack Details:
Stored XSS arises when an application receives data from an untrusted source and includes that data within its later HTTP responses in an unsafe way. The data in question might be submitted to the application via HTTP requests; for example in our vulnerable application users can use the **Discussion Section** to post comments which get saved to the database. All comments are visible to every registered user, hence if an attacker has injected Javascript via comment it gets saved to the database, and whenever any user loads this discussion section server will return this script. An attacker can craft the Javascript to perform **RCE** that may steal cookies, saved passwords, or CSRF tokens and relay them back to the attacker-controlled domain.

Deep diving into our application code we see the 2 main causes of this vulnerability.
* **No validation/sanitization** of user data before inserting it into database.
```
  # get user comment and insert into discussion table
  comment = request.form['discussion']
  user_id = session["id"]
  user_name = session["username"]
  cursor.execute('INSERT INTO discussions VALUES (NULL, %s, %s, %s)', (user_id, user_name, comment))
  connection.commit()
 ```
            
* **Considering user data to be safe** by using `|safe` tag that renders string without escaping.
```
  {% for row in data %}
    <div>
        <p>{{ row[2] }} commented:</p>
        <p>{{ row[3]|safe }}</p>
    </div>
  {% endfor %}
```
#### Remediation Steps:
* **Filter input on arrival.** At the point where user input is received, filter as strictly as possible based on what is expected or valid input
  - Construct strict **Syntax and Semantic** rules to validate user input.
  - Construct **Whitelisting and Blacklisting** of expected and unexpected user data.
  - Construct **Regular expressions** to validate user input.

* **Output Encoding for “HTML Contexts”.**  Output Encoding is recommended when we need to safely display data exactly as a user typed it in.
Hence in order to add a variable to a HTML context safely, HTML entity encoding should be used for that variable as we add it to a web template. Flask has default encoding capability, hence to fix the vulnerability in our code we should remove the `|safe` tag while adding it to web template.

