"""Bounded metadata search for the central skill library."""

def search(index,query='',limit=8,status=None):
    if not 1<=limit<=50:raise ValueError('Limit must be between 1 and 50')
    terms=query.casefold().split();ranked=[]
    for row in index['skills']:
        if status and row['status']!=status:continue
        hay=(row['id']+' '+row['description']+' '+' '.join(row.get('tags',[]))).casefold()
        if not all(t in hay for t in terms):continue
        score=sum(4 if t in row['id'] else 1 for t in terms)+(2 if row['status']=='reviewed' else 0)
        ranked.append((score,row))
    return [r for _,r in sorted(ranked,key=lambda x:(-x[0],x[1]['id']))[:limit]]
