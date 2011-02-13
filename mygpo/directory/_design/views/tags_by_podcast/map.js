function(doc)
{
    function searchPodcast(podcast, podcast_id)
    {
        for(source in podcast.tags)
        {
            for(n in podcast.tags[source])
            {
                emit([podcast_id, podcast.tags[source][n]], sourceWeight(source));
            }
        }
    }

    function sourceWeight(source)
    {
        if(source == "user")
        {
            return 0.5;
        }
        else if(source == "feed")
        {
            return 1;
        }
        else if (source == "delicious")
        {
            return 2;
        }
        else
        {
            return 0;
        }
    }

    if(doc.doc_type == "Podcast")
    {
        searchPodcast(doc, doc._id);
    }
    else if(doc.doc_type == "PodcastGroup")
    {
        for(p in doc.podcasts)
        {
            searchPodcast(p, p.id);
        }
    }
    else if(doc.doc_type == "PodcastUserState")
    {
        for(n in doc.tags)
        {
            emit([doc.podcast, doc.tags[n]], sourceWeight("user"));
        }
    }
}
