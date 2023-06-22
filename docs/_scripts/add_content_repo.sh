# Add created Gem content to repository
pulp gem repository content add --repository foo --href $CONTENT_HREF

# After the task is complete, it gives us a new repository version
pulp gem repository version show --repository foo
