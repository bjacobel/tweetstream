#Tweetstream
###(A.K.A. Wire100)

---

####Requirements
* [twitter](https://github.com/sixohsix/twitter), the Python Twitter API wrapper
* [PyLevenshtein](https://github.com/miohtama/python-Levenshtein?source=c)
* [Redis](https://github.com/andymccurdy/redis-py)
* Python 2.7
* Valid OAuth credentials in write mode

####About
Command line Python program for finding interesting tweets in the Twitter streaming API. Listens to a stream of tweets from and retweeted by [seed accounts](https://github.com/bjacobel/tweetstream/blob/master/ids.txt), assigns each tweet a value (based on an almost completely arbitrary scoring mechanism) and compares that score to the rate of the stream. 

If the value of the tweet is higher than the bar set by the rate of tweets recieved in the past five minutes, the tweet is retweeted by the Twitter account specified in the [OAuth credentials](https://github.com/bjacobel/tweetstream/blob/master/myoauth.py) file.

Because finding the Twitter IDs of accounts you'd like to follow is hard, Tweetstream provides a method for listing usernames in [a file](https://github.com/bjacobel/tweetstream/blob/master/users.txt), then running [a script](https://github.com/bjacobel/tweetstream/blob/master/users_to_ids.py) on them to convert them to User IDs.

####Developed
during my internship at The Atlantic as a prototype for an Atlantic Wire site module. If you are an Atlantic Programmer looking to continue my work, check [Redmine](http://atldevbox1.amc/projects/general/wiki/Passwords_keys_and_docs) for both OAuth credentials and access to the [wirecurator](http://twitter.com/wirecurator) account.