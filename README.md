TaskWarrior - Google Calendar synchronizer

**Current module is still under heavy development. That means that the following
instructions are merely project specifications and not ready-to-use features**

Current repo is an attempt at synchronizing reminders across TaskWarrior and
Google Calendar. The reason for the latter combination is that, while
TaskWarrior is an excellent tool when it comes to keeping todo lists, keeping
track of project goals etc., lacks the portability and simplicity of Google
Calendar and its reminders. The latter also has the following advantages:

- Automatic sync across all your devices
- Super easy addition of new reminders using voice commands
- Actual reminding of reminders and flexibility in defining the reminder time

Current script takes care of:

- Adding/Modifying reminders across the two services
- Mark reminders as done
- Deleting reminders

The aforementioned features should work bidirectional, meaning a reminder addded
by TW is uploaded to GCal where it can be modified. The TW reminder is then to
be updated based on the modified content.

To achive synchronization across the two services, we use a push-pull mechanism
which is far easier and less troublesome than an automatic synchronization
solution. In case the latter behavior is desired, users may just run the `TODO`
script periodically e.g. using a cronjob.

% TODO - Add synchronization instructions
