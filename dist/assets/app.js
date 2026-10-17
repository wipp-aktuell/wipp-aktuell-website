const search = document.querySelector('#search');
if(search){search.addEventListener('input',()=>{const val=search.value.toLocaleLowerCase('de').trim();let visible=0;document.querySelectorAll('[data-search]').forEach(item=>{const match=item.dataset.search.includes(val);item.hidden=!match;if(match)visible++});document.querySelector('#no-results').hidden=visible!==0;});}
