# la_casa_lobot
discord bot for my friends' and I's server

Nothing fancy, integrates some movie watchlist commands into our discord server
The bot is being hosted on a digital ocean droplet

the commands so far are:

$watchlist username

takes a letterboxd username and webscrapes for the watchlist of the user

$watchlist_pool username1,username2,...

takes a list of letterboxd usernames separated by a comma and webscrapes for the watchlist of the users

$random_watchlist username

webscrapes for the watchlist, then returns a random movie

$random_watchlist_pool username1,username2,...

webscrapes multiple users letterboxd watchlists then prints a random movie, ensuring no duplicates are present in the original watchlist

$coinflip

simple coinflip with a little animation to spice it up

Recommendation Commands:

$recommend movie, number_of_recommendations

provide recommendations for a movie, detailed explanation on this command in the other readme
