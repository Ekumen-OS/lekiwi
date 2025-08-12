# parsing Git information
parse_git_branch() {
  git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

unstaged() {
    if [[ $(git status -s 2> /dev/null | wc -c) != 0 ]]; then echo " +"; fi
}

export PS1='\[\033[01;36m\](docker)\[\033[00m\] \[\033[01;32m\]\u@lekiwi-${USER}\[\033[00m\]:\[\033[01;34m\]\w\[\033[33m\]$(parse_git_branch)$(unstaged)\[\033[00m\] \$ '
alias ll='ls --color=auto -alFNh'
alias ls='ls --color=auto -Nh'
