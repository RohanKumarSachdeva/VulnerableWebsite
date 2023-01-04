# VulnerableWebsite
* This is a `Student Management` website built on Flask and MySQL database for demonstrating OWASP vulnerabilities.
* The website features user registration and login, profile viewing and discussion posting functionalities.
* Username `admin` with password `admin123` gets initialized when application is deployed.
* `admin` user can view profiles for all registered users on its `Profile` page. All other users can only view their own profile details.
* Every user can post comments and view comments posted by all other users on `Discussions` page.

## How to run
* Prerequisite: Install Docker.
* Clone this repository `https://github.com/RohanKumarSachdeva/VulnerableWebsite`.
* Change the directory to `VulnerableWebsite`
* Run `docker-compose up`
* Browse to `http://127.0.0.1:5000/` to access the application.

## OWASP vulnerabilities Detail and their Remediation
### 1. SQL Injection:
#### Attack Details:
Our vulnerable application lets users log in with a username and password. If a user submits the username `adam` and the password `qwerty`, the application checks the credentials by concatenating them as shown below, and forms a SQL query:
> "SELECT * FROM accounts WHERE username=" + username + " AND password=" + password

Which transforms to:
> SELECT * FROM users WHERE username = 'adam' AND password = 'qwerty'

If the query returns the details of a user, then the login is successful. Otherwise, it is rejected.

Here, an attacker can log in as any user without a password simply by using the SQL comment sequence `-- ` which will comment out the password check from the `WHERE` clause of the query. For example, submitting the username **`admin'-- `** (make sure to add a ` ` space character after `--`) ,and a blank/wrong password results in the following query:
> SELECT * FROM users WHERE username = 'admin'-- ' AND password = ''

This query returns the user details **in-band**, if its username `admin` exists in the database and successfully logs the attacker in as that user. Since `admin` user has capability to view details of all registered users, the attacker will now be able to view this information.

#### Remediation Steps: Following are the best practices to avoid SQL Injection
* **Using Prepared/Parameterized statements**. These are pre-compiled SQL statements. The query is already pre-compiled, so the final query will not go through the compilation phase again. For this reason, the user-provided data will always be interpreted as a simple string and cannot modify the original query’s logic. Hence to fix the vulnerability in our application we can use the following parameterized statement where `%s` are placeholders used for parameters that will be supplied during execution time.
> 'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password)

* **Escaping of user data**. If a parameterized API is not available, we should carefully escape special characters present in the user supplied input. Escaping involves adding a special character before the character/string to avoid it being misinterpreted, for example, adding a `\` character before a `"(double quote)` character so that it is interpreted as text and not as closing a string.

* **HtmlEncode all user input.** Encoding (commonly called “Output Encoding”) involves translating special characters into some different but equivalent form that is no longer dangerous in the target interpreter, for example translating the `<` character into the `&lt`. We can use this technique to further sanitize user input in our application.


### 2. Stored Cross Site Scripting (XSS): can cause RCE
#### Attack Details:
In our vulnerable application users can use the **Discussion Section** to post comments which get saved to the database. All comments are visible to every registered user, hence if an attacker has injected Javascript (example `<script>alert('Hacked')</script>`) via comment it gets saved to the database, and whenever any user loads this discussion section server will return this script. An attacker can use Stored XSS to perform **RCE** that may steal cookies, saved passwords, or CSRF tokens and relay them back to the attacker-controlled domain.

Deep diving into our application code we see the 2 main causes of this vulnerability.
* **No validation/sanitization** of user data before inserting it into the database.
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
Hence, in order to add a variable to an HTML context safely, HTML entity encoding should be used for that variable as we add it to a web template. Flask has [default encoding](https://flask.palletsprojects.com/en/1.1.x/templating/#controlling-autoescaping) capability, hence to fix the vulnerability in our code we should remove the `|safe` tag so that Flask can encode the string value before adding it to HTML.

### 3. Session Fixation:
#### Attack Details:
Our application is vulnerable to **session fixation** which can be explioted by using tools like **flask-unsign**. [Flask-unsign](https://pypi.org/project/flask-unsign/) is a command line tool to fetch, decode, brute-force and craft session cookies of a Flask application by guessing secret keys. Below are the steps on how to exploit the session vulnerability in our flask application:

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
  - Use [wordlist](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&ved=2ahUKEwjstLrx8af8AhX8-DgGHQJyA0UQFnoECBMQAQ&url=https%3A%2F%2Fgithub.com%2Fbrannondorsey%2Fnaive-hashcat%2Freleases%2Fdownload%2Fdata%2Frockyou.txt&usg=AOvVaw3snAERl1mU6Ccr4WFEazBd) of common passwords to bruteforce the secret key.
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
- Using [strong and random](https://flask.palletsprojects.com/en/0.12.x/quickstart/#sessions) API secret_key to avoid bruteforce attacks.
- Session ID must be long enough to prevent brute force attacks. The session ID length must be at least 128 bits (16 bytes).
- The session ID must be unpredictable (random enough) to prevent guessing attacks. For this purpose, a good CSPRNG (Cryptographically Secure Pseudorandom Number Generator) should be used to create session IDs.
- Also, an active session should be warned when it is accessed from another location.

### Docker Security Considerations:

* **Using minimal base images:** We have used official Debian based Python 3.9-slim-buster image in our application. By preferring minimal images that bundle only the necessary system tools and libraries required to run our project, we also minimize the attack surface for attackers.

* **Having least privileged user:** When a `Dockerfile` does not specify a `USER`, it defaults to executing the container using the root user. This further broadens the attack surface and enables an easy path to privilege escalation. Hence, in our application we can use the `USER` directive in the `Dockerfile` to ensure the container runs the application with the least privileged access possible.

* **Issue with recursive copy:** We should also be mindful when copying files into the image that is being built. The command `COPY . .` copies the entire build context folder, recursively, to the Docker image, which could end up copying sensitive files as well. Hence, we can use .dockerignore to ignore the sensitive files while building them.

* **Leaking sensitive information to Docker images:** Sometimes when building an application inside a Docker image, we need secrets like private keys or passwords. If we copy them into the Docker intermediate container they are cached on the layer to which they were added, even if we delete them later on. Therefore, we can make use of [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/) to manage these sensitive data.

* **Runtime consideration with multi-containers:** It is difficult to control the speed at which different containers start. In our application we faced issue where flask application was starting before mysql container could be ready to serve requests. Container orchestration solution like Kubernetes might be able to help us in such cases. Kubernetes has the concept of [init containers](https://www.handsonarchitect.com/2018/08/understand-kubernetes-object-init.html) which run to completion before the dependent container can start.

### CI/CD & Kubernetes Deployment Considerations:

The current setup is a local deployment of 2 containers, one for the mysql database and the other is the actual service which has vulnerabilities. We can integrate CI/CD and deploy this on Kubernetes to make the service robust and allow for smooth software development/updates on the service. Following are some considerations:

* Allocate a set of servers or VMs which can serve as a Kubernetes cluster
* Decouple the deployment of MySQL DB and the Vulnerable service
* Deploy the service as a Kubernetes deployment on the cluster
* Write basic unit and integration tests and plug them with Github Actions to allow for testing whenever a PR is merged to the main branch
* Once those tests succeed, we can use Jenkins or Github Actions to deploy the code on the Kubernetes cluster
* Code deployment would involve packaging the latest code as a new docker image (new tag for a minor update or a totally new image for a major update)
* Update the service as a Kubernetes deployment (with 3 or more replicas) by performing rolling update on the same using the following command: `kubectl set image deployment/<service_deployment_name> app:<new_tag> --record`
