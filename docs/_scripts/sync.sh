# Using the Remote we just created, we kick off a sync task
pulp gem repository sync --name foo --remote gem

# The sync command will by default wait for the sync to complete
# Use Ctrl+c or the -b option to send the task to the background

# Show the latest version when sync is done
pulp gem repository version show --repository foo
