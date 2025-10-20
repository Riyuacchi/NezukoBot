pub mod embeds;

pub fn format_number(n: i64) -> String {
    let s = n.to_string();
    let mut result = String::new();
    let chars: Vec<char> = s.chars().collect();
    let len = chars.len();

    for (i, c) in chars.iter().enumerate() {
        if i > 0 && (len - i) % 3 == 0 && *c != '-' {
            result.push(',');
        }
        result.push(*c);
    }

    result
}

pub fn to_db_id(id: u64) -> i64 {
    id as i64
}
