import logging

import numpy as np
import scipy.sparse


def matrix_to_lists(doc_word):
    """Convert a (sparse) matrix of counts into arrays of word and doc indices

    Parameters
    ----------
    doc_word : array (D, V)
        document-term matrix of counts

    Returns
    -------
    (WS, DS) : tuple of two arrays
        WS[k] contains the kth word in the corpus
        DS[k] contains the document index for the kth word

    """
    if np.count_nonzero(doc_word.sum(axis=1)) != doc_word.shape[0]:
        logging.warn("all zero row in document-term matrix found")
    if np.count_nonzero(doc_word.sum(axis=0)) != doc_word.shape[1]:
        logging.warn("all zero column in document-term matrix found")
    try:
        doc_word = doc_word.tocoo()
    except AttributeError:
        doc_word = scipy.sparse.coo_matrix(doc_word)
    ii, jj, ss = doc_word.row, doc_word.col, doc_word.data
    n_tokens = doc_word.sum()
    DS = np.zeros(n_tokens, dtype=int)
    WS = np.zeros(n_tokens, dtype=int)
    startidx = 0
    for i, cnt in enumerate(ss):
        DS[startidx:startidx + cnt] = ii[i]
        WS[startidx:startidx + cnt] = jj[i]
        startidx += cnt
    return WS, DS


def lists_to_matrix(WS, DS):
    """Convert array of word (or topic) and document indices to doc-term array

    Parameters
    -----------
    (WS, DS) : tuple of two arrays
        WS[k] contains the kth word in the corpus
        DS[k] contains the document index for the kth word

    Returns
    -------
    doc_word : array (D, V)
        document-term array of counts

    """
    D = max(DS) + 1
    V = max(WS) + 1
    doc_word = np.zeros((D, V), dtype=int)
    for d in range(D):
        for v in range(V):
            doc_word[d, v] = np.count_nonzero(WS[DS == d] == v)
    return doc_word


def dtm2ldac(dtm):
    try:
        dtm = dtm.tocsr()
    except AttributeError:
        pass
    num_rows = dtm.shape[0]
    for i, row in enumerate(dtm):
        try:
            row = row.toarray().squeeze()
        except AttributeError:
            pass
        unique_terms = np.count_nonzero(row)
        if unique_terms == 0:
            raise ValueError("dtm contains row with all zero entries.")
        term_cnt_pairs = [(i, cnt) for i, cnt in enumerate(row) if cnt > 0]
        docline = str(unique_terms) + ' '
        docline += ' '.join(["{}:{}".format(i, cnt) for i, cnt in term_cnt_pairs])
        if (i + 1) % 1000 == 0:
            logging.info("dtm2ldac: on row {} of {}".format(i + 1, num_rows))
        yield docline


def ldac2dtm(stream):
    """Convert lda-c formatted file to a document-term array

    Parameters
    ----------
    stream : file object
        Object that has a `read` method.

    Returns
    -------
    dtm : array of shape N,V
    """
    doclines = [docline for docline in stream.read().split('\n') if docline]
    # we need to figure out the dimensions of the dtm. N is easy, V takes a pass
    N = len(doclines)
    data = []
    for l in doclines:
        term_cnt_pairs = [s.split(':') for s in l.split(' ')[1:]]  # 1: skips first term in line
        term_cnt_pairs = [(int(v), int(cnt)) for v, cnt in term_cnt_pairs]
        data.append(term_cnt_pairs)
    V = -1
    for doc in data:
        vocab_indicies = [V] + [v for v, cnt in doc]
        V = max(vocab_indicies)
    V = V + 1
    dtm = np.zeros((N, V), dtype=int)
    for i, doc in enumerate(data):
        for v, cnt in doc:
            np.testing.assert_(dtm[i, v] == 0)
            dtm[i, v] = cnt
    return dtm
