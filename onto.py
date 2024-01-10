from owlready2 import get_ontology, Thing, FunctionalProperty


def create_base(path_to_save: str) -> None:
    onto = get_ontology("http://www.example.org/new-book-ontology#")

    with onto:
        class Ksiazka(Thing):
            pass

        class Autor(Thing):
            pass

        class Kategoria(Thing):
            pass

        class SlowoKluczowe(Thing):
            pass

        class Seria(Thing):
            pass

        class Wydawnictwo(Thing):
            pass

        # Właściwości Książka
        class maTytul(Ksiazka >> str, FunctionalProperty):
            pass

        class maAutora(Ksiazka >> Autor, FunctionalProperty):
            pass

        class maOcene(Ksiazka >> float, FunctionalProperty):
            pass

        class maWydawnictwo(Ksiazka >> Wydawnictwo, FunctionalProperty):
            pass

        class maSerie(Ksiazka >> Seria, FunctionalProperty):
            pass

        class maLiczbeStron(Ksiazka >> int, FunctionalProperty):
            pass

        class maSlowoKluczowe(Ksiazka >> SlowoKluczowe):
            pass

        class maKategorie(Ksiazka >> Kategoria, FunctionalProperty):
            pass

        # Właściwości Autor
        class maImieNazwisko(Autor >> str, FunctionalProperty):
            pass

        class maURL(Autor >> str, FunctionalProperty):
            pass

        # Właściwości Kategoria
        class maNazwe(Kategoria >> str, FunctionalProperty):
            pass

        class maURLK(Kategoria >> str, FunctionalProperty):
            pass

        # Właściwości Seria
        class maTytulSerii(Seria >> str, FunctionalProperty):
            pass

        # Właściwości Wydawnictwo
        class maNazweW(Wydawnictwo >> str, FunctionalProperty):
            pass

        # Właściwości Słowa Kluczowe
        class maNazweSlowa(SlowoKluczowe >> str, FunctionalProperty):
            pass

    onto.save(file=path_to_save, format="rdfxml")


def add_instance(onto_path: str, onto_iri: str, book_dict: dict()) -> None:
    onto = get_ontology(onto_iri).load(onto_path)

    with onto:
        ksiazka = onto.Ksiazka()

        ksiazka.maTytul = book_dict['title']
        ksiazka.maOcene = book_dict['rating']
        ksiazka.maLiczbeStron = book_dict['page_number']

        # Autor
        author_instance = onto.search_one(
            iri='*autor*', maImieNazwisko=book_dict['author']
        )
        if author_instance:
            ksiazka.maAutora = author_instance
        else:
            ksiazka.maAutora = onto.Autor(maImieNazwisko=book_dict['author'],
                                          maURL=book_dict['author_url'])

        # Kategoria
        cat_instance = onto.search_one(
            iri='*kategoria*',
            maNazwe='turystyka, mapy, atlasy'
        )
        if cat_instance:
            ksiazka.maKategorie = cat_instance
        else:
            ksiazka.maKategorie = onto.Kategoria(
                maNazwe=book_dict['category'],
                maURLK=book_dict['category_url']
            )

        # Seria
        series_instance = onto.search_one(
            iri='*seria*', maTytulSerii=book_dict['author']
        )
        if series_instance:
            ksiazka.maSerie = series_instance
        else:
            ksiazka.maSerie = onto.Seria(
                maTytulSerii=book_dict['series']
            )

        # Wydawnictwo
        publisher_instance = onto.search_one(
            iri='*wydawnictwo*',
            maNazweW=book_dict['publisher'])
        if publisher_instance:
            ksiazka.maWydawnictwo = publisher_instance
        else:
            ksiazka.maWydawnictwo = onto.Wydawnictwo(
                maNazweW=book_dict['publisher']
            )

        # Słowa kluczowe
        for keyword in book_dict['keywords']:
            keyword_instance = onto.search_one(
                iri='*slowokluczowe*',
                maNazweSlowa=keyword
            )

            if keyword_instance:
                ksiazka.maSlowoKluczowe.append(keyword_instance)
            else:
                ksiazka.maSlowoKluczowe.append(
                    onto.SlowoKluczowe(maNazweSlowa=keyword))

    onto.save(file=onto_path, format="rdfxml")
