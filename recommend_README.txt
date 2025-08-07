The recommendation engine uses a dataset gathered from TMDB, which was gathered by the miner.py file, on a Digital Ocean virtual machine

Preamble:
While making this I considered incorporating machine learning aspects to make the recommendations more accurate, there are a few reasons I opted against this.
The server I am hosting the discord bot on, is 1 vCPU and 1 gB of RAM, I want the bot to be as responsive as possible and using ML would be more resource intensive
than the current Top-N storage solution. Secondly, ML would be useful if I intended to include user input (hybrid-filtering model) for the movie recommendations, 
but because of the medium the engine is running on (discord bot) user personalization would be unnecessarily difficult. If I intended to scale the bot up and use 
it on multiple servers, I would need solutions for user data collection and storage. Perhaps for another project I will consider creating a more accurate engine 
that uses hybrid-filtering, but for this context, content-filtering will suffice.

The recommendations are content-filtered and selected based on 3 similarity matrixes
The weightings of the count vectors, and the similarity matrices are decided manually, I intend to find a solution that will make the weightings optimal

Text based matrix:
- the text based matrix uses 'keywords', 'cast', 'genres', 'director', 'production_companies', 'origin_country', 'overview'
- the values in these cells are tokenized and added to another column in the dataframe
* the overview has stopwords removed before this

Ex.
-------------------------------------------------------------------------------------------------------------------------------------------------------
|    title    |  keywords  |    cast    | genres |   director  |production_companies|origin_country|      overview      |          combined           |
-------------------------------------------------------------------------------------------------------------------------------------------------------
|'fake movie' |'underwater'|'matt damon'|'action'|'micheal bay'|    'paramount'     |     'US'     |'kyle is underwater'|'underwater', 'matt damon'...|
-------------------------------------------------------------------------------------------------------------------------------------------------------

- to change the weighting of a feature the entries are multiplied by the following dictionary so that the count vector reflects the weights

word_weight = {
        'keywords': 5,
        'cast': 3,
        'genres': 4,
        'director': 4,
        'production_companies': 1,
        'origin_country': 1,
        'overview': 5
    }

Ex. Count vector of the combined column:

---------------------------------------------------------------
|underwater|matt damon|action|michael bay|paramount| US | kyle|
---------------------------------------------------------------
|  2*5=10  |   1*3=3  | 1*4=4|   1*4=4   |  1*1=1  |  1 |1*5=5|
---------------------------------------------------------------

- this vector is then compared to the vector of every other movie in the data set using cosine similarity

Ex. Cosine similarity formula
( A * B ) / ( ||A|| * ||B|| )
where A and B are vectors of word counts

- below is an example of the matrix this will create

Ex.

--------------------------------------------------
|          |  tron  | fight club |  alien  | ... |
--------------------------------------------------
|   tron   |    1   |   0.2366   |  0.4333 | ... |
--------------------------------------------------
|fight club| 0.2366 |      1     |  0.3374 | ... |
--------------------------------------------------
|  alien   | 0.4333 |   0.3374   |    1    | ... |
--------------------------------------------------
|    ...   |   ...  |     ...    |   ...   | ... |
--------------------------------------------------

- to use this matrix, look at the row and column to see which movies are being compared.

Number based matrix:
- the number based matrix uses 'vote_average', 'popularity'
- vote average is the average score people rated a given movie, and is on a scale from 1-10, this is reduced to 0-1
- while popularity is a metric from TMDB that is scaled logarithmically, then using a min-max scaler so that it is also 0-1
- in a similar way, the normalized values for each movie are compared using cosine similarity, to see if movies are similar in popularity and are similarly rated

Ex. example of the matrix this will create

--------------------------------------------------
|          |  tron  | fight club |  alien  | ... |
--------------------------------------------------
|   tron   |    1   |   0.2501   |  0.2905 | ... |
--------------------------------------------------
|fight club| 0.2501 |      1     |  0.5830 | ... |
--------------------------------------------------
|  alien   | 0.2905 |   0.5830   |    1    | ... |
--------------------------------------------------
|    ...   |   ...  |     ...    |   ...   | ... |
--------------------------------------------------

Time based matrix:
- the time difference between when movies were made will also impact the similarity of movies
- the difference between release years is scaled using the an exponential decay formula

Ex.
similarity = exp( -alpha * time_difference )

- where the alpha variable dictates how severely a time difference is punished

Ex.
--------------------------------------------------
|          |  tron  | fight club |  alien  | ... |
--------------------------------------------------
|   tron   |    1   |   0.4274   |  0.8607 | ... |
--------------------------------------------------
|fight club| 0.4274 |      1     |  0.3678 | ... |
--------------------------------------------------
|  alien   | 0.8607 |   0.3678   |    1    | ... |
--------------------------------------------------
|    ...   |   ...  |     ...    |   ...   | ... |
--------------------------------------------------

Total similarity matrix:
- the final matrix is essentially an overlapping of the three similarity matrices
- the matrices are given different weights, as follows below

w_text = 0.8
w_num = 0.15
w_time = 0.05

Ex. formula for applying the weights to the matrices
sim_matrix_total = (w_text * sim_matrix_text + w_num * sim_matrix_num + w_time * sim_matrix_time)

*total of all the weights to not exceed 1

The Recommendation process:
- considering the dataset is approximately 10000 movies long, the similarity matrix will occupy a lot of memory when it is accessed
  this will be solved by preprocessing the similarity matrix for each movie's Top-N (Where N is 20) most similar results, this will
  be stored in a json object for efficient storage and access.
- when the command is called, the inputted movie title is cleaned and then converted to its index so it can be used to acces the json
  object's similar movies. Which are then printed to the user