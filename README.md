<h1>WebChat</h1>

<h2>Overview</h2>
<p>This repository contains the code for a discussion application, which facilitates the creation and interaction within various discussion areas based on different topics. Each area contains threads consisting of messages. Users can either be administrators or basic users, with administrators having additional privileges.</p>

<h2>Live Demo</h2>
<p>The live project can be accessed at <a href="https://nikoweb.eu/projects/webchat/">https://nikoweb.eu/projects/webchat/</a></p>

<h2>Installation & Setup</h2>

<details>
  <summary><strong>Minimal Setup</strong></summary>
  <p>This setup is for quickly getting the application running with a basic configuration. It is not a secure configuration and for a real deployment the settings should be customized.</p>
  <ol>
    <li>
      <strong>Clone the Repository:</strong>
      <pre><code>git clone https://github.com/Roar1ngDuck/webchat</code></pre>
    </li>
    <li>
      <strong>Configure Environment:</strong>
      <p>Copy <code>.env.example</code> to <code>.env</code>:</p>
      <pre><code>cp .env.example .env</code></pre>
    </li>
    <li>
      <strong>Run Docker Compose:</strong>
      <p>Use Docker Compose to start the application:</p>
      <pre><code>docker compose up</code></pre>
    </li>
    <li>
      <strong>Access</strong>
      <p>The app will be accessible at http://127.0.0.1:8001/ by default</p>
    </li>
  </ol>
</details>

<details>
  <summary><strong>Advanced Setup</strong></summary>
  <p>Detailed setup steps for a more customized configuration:</p>
  <ol>
    <li>
      <strong>Clone the Repository:</strong>
      <pre><code>git clone https://github.com/Roar1ngDuck/webchat</code></pre>
    </li>
    <li>
      <strong>Configure Environment Variables:</strong>
      <p>Set up the environment variables by copying the example files:</p>
      <ul>
        <li><code>.env</code> for running the application. Copy <code>.env.example</code> to <code>.env</code>.</li>
        <li><code>.env.test</code> for running tests. Copy <code>.env.test.example</code> to <code>.env.test</code>.</li>
      </ul>
      <pre><code>cp .env.example .env
cp .env.test.example .env.test</code></pre>
      <h4>Required Variables in .env:</h4>
      <ul>
        <li><strong>SECRET_KEY:</strong> Flask secret key.</li>
        <li><strong>ADMIN_PASSWORD:</strong> Default admin user password.</li>
      </ul>
      <h4>Optional Variables:</h4>
      <ul>
        <li><strong>DB_URL:</strong> External database URL (if not using Docker with predefined value in Dockerfile).</li>
        <li><strong>USE_TURNSTILE:</strong> <code>True</code>/<code>False</code> to toggle Cloudflare CAPTCHA (Turnstile)</li>
        <li><strong>TURNSTILE_SECRET:</strong> Turnstile secret key.</li>
        <li><strong>TURNSTILE_SITEKEY:</strong> Turnstile site key.</li>
        <li><strong>ENV:</strong> Environment setting, which affects certain application behaviors:
          <ul>
            <li><strong>PROD:</strong> Sets secure cookie attributes (SECURE, HTTP_ONLY, SAMESITE) for enhanced security.</li>
            <li><strong>DEV:</strong> Does not set secure cookie attributes, suitable for development environments.</li>
            <li><strong>TEST:</strong> Used for pytest; does not set secure cookie attributes and resets the database with each execution.</li>
          </ul>
        </li>
      </ul>
    </li>
    <li>
      <strong>Run Docker Compose:</strong>
      <p>Start the application with Docker Compose:</p>
      <pre><code>docker compose up</code></pre>
    </li>
    <li>
      <strong>Access</strong>
      <p>The app will be accessible at http://127.0.0.1:8001/ by default</p>
    </li>
    <li>
      <strong>Running Tests:</strong>
      <p>For running tests the app needs to be executed without Docker. For this, make sure you have a postgres database which corresponds to the name in ".env.test", which by default is "webchat_test".</p>
      <p>To run the test suite, execute pytest:</p>
      <pre><code>pytest</code></pre>
    </li>
  </ol>
</details>

<h2>Features</h2>
<h3>User Account Management</h3>
<ul>
  <li><strong>User Registration:</strong> Allows new users to create an account.</li>
  <li><strong>Login/Logout:</strong> Users can log in to access the application and log out after they're done.</li>
  <li><strong>Admin Users:</strong> Administrator users with additional privileges.</li>
</ul>

<h3>Discussion Areas</h3>
<ul>
  <li><strong>Area Creation:</strong> Administrators can create new discussion areas.</li>
  <li><strong>Secret Areas:</strong> Administrators can create secret areas with restricted user access.</li>
  <li><strong>Viewing Areas:</strong> Users can see a list of all discussion areas on the homepage along with the number of threads and messages in each area, and when the last message was sent.</li>
  <li><strong>Thread Creation:</strong> Users can create a new thread in an area by providing a thread title and the content of the initial message.</li>
  <li><strong>Search:</strong> Users can search area topics, thread titles, and message content for given text.</li>
  <li><strong>Subscriptions:</strong> Users can subscribe to threads and they will receive a notification when another user posts a message.</li>
</ul>

<h3>Messaging</h3>
<ul>
  <li><strong>Posting Messages:</strong> Users can write a new message in an existing thread and edit previously sent ones. Messages can optionally include images.</li>
  <li><strong>Message Deletion and Editing:</strong> Users can delete their messages and threads they have created.</li>
  <li><strong>Thread and Area Deletion:</strong> Administrators can delete threads and areas.</li>
</ul>

<h2>Implementation Details</h2>
<ul>
  <li><strong>Database Schema:</strong> Defined and initialized in <code>utils/db.py</code>, including the creation of tables and an admin user. The Database class is implemented as a singleton.</li>
  <li><strong>Password Hashing:</strong> User passwords are securely hashed using bcrypt.</li>
  <li><strong>CAPTCHA Verification:</strong> Cloudflare Turnstile is integrated to prevent automated spam and bot registrations</li>
  <li><strong>Password Strength Measurement:</strong> Password strength is evaluated using the zxcvbn library, which estimates password crack times based on various factors such as dictionary words, predictable patterns, and password length.</li>
  <li><strong>Gunicorn:</strong> Gunicorn is used as the WSGI HTTP server, enhancing the ability to handle concurrent requests efficiently compared to the default Flask server.</li>
</ul>
