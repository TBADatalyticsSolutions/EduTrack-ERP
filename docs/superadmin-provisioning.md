# EduTrack ERP

## Safe platform super-admin provisioning

Create or synchronize the platform-level administrator with the Django management command:

```bash
python manage.py provision_superadmin --username Admin01 --email admin@example.com
```

For a new account, the command prompts for the password twice. The password is never accepted as a command-line argument.

The command is safe to repeat. If the named account is already a superuser, it synchronizes the platform role/profile without creating a duplicate account.

### Production / Render

Run the command from the Render Shell after migrations have completed:

```bash
python manage.py provision_superadmin --username Admin01 --email admin@example.com
```

For non-interactive automation, provide the password through the secret environment variable `DJANGO_SUPERADMIN_PASSWORD` and use `--noinput`:

```bash
python manage.py provision_superadmin --username Admin01 --email admin@example.com --noinput
```

Do **not** put the password in the command itself or commit the environment variable to source control.

### Existing accounts

An existing non-superuser account is **not** promoted by default. The command fails rather than silently escalating privileges.

Only after verifying the account is the intended platform administrator should an operator explicitly use:

```bash
python manage.py provision_superadmin --username Admin01 --promote-existing
```

To reset an existing super-admin password, use `--reset-password`. The password is prompted securely, or supplied through `DJANGO_SUPERADMIN_PASSWORD` with `--noinput`.

The provisioned account is platform-scoped: its `SUPER_ADMIN` role is assigned and its school is cleared.
