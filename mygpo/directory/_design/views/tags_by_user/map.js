function (doc)
{
    if (doc.doc_type == "PodcastUserState")
    {
        for(n in doc.tags)
        {
            emit([doc.user_oldid, doc.podcast], doc.tags[n]);
        }
    }
}
