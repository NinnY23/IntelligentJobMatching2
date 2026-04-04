:- module(matching, [suitable/4, missing_skills/3]).

%% suitable(+CandidateSkills, +RequiredSkills, +PreferredSkills, -Score)
%%
%% Score is a float in [0, 100].
%%   70% weight  →  fraction of RequiredSkills present in CandidateSkills
%%   30% weight  →  fraction of PreferredSkills present in CandidateSkills
%% This predicate ONLY succeeds when Score >= 50.
%%
suitable(CandidateSkills, RequiredSkills, PreferredSkills, Score) :-
    intersection(CandidateSkills, RequiredSkills, MatchedRequired),
    intersection(CandidateSkills, PreferredSkills, MatchedPreferred),
    length(RequiredSkills, RLen),
    (   RLen > 0
    ->  length(MatchedRequired, MRLen),
        RequiredScore is (MRLen / RLen) * 70
    ;   RequiredScore is 70          % no requirements → full required score
    ),
    length(PreferredSkills, PLen),
    (   PLen > 0
    ->  length(MatchedPreferred, MPLen),
        PreferredScore is (MPLen / PLen) * 30
    ;   PreferredScore is 0          % no preferred → 0 bonus
    ),
    Score is RequiredScore + PreferredScore,
    Score >= 50.

%% missing_skills(+CandidateSkills, +RequiredSkills, -Missing)
%%
%% Missing is the subset of RequiredSkills not present in CandidateSkills.
%%
missing_skills(CandidateSkills, RequiredSkills, Missing) :-
    subtract(RequiredSkills, CandidateSkills, Missing).
