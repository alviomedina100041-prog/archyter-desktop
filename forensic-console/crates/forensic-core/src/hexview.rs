use crate::HexChunk;
use anyhow::{bail, Context, Result};
use std::{
    fs::File,
    io::{Read, Seek, SeekFrom},
    path::Path,
};

pub fn read_file_chunk(path: &Path, offset: u64, length: usize) -> Result<HexChunk> {
    let length = length.clamp(1, 4096);
    let mut file = File::open(path).with_context(|| format!("cannot open {}", path.display()))?;
    let file_len = file.metadata()?.len();

    if offset > file_len {
        bail!("offset is beyond end of file");
    }

    file.seek(SeekFrom::Start(offset))?;
    let mut buffer = vec![0_u8; length];
    let read = file.read(&mut buffer)?;
    buffer.truncate(read);

    Ok(HexChunk {
        offset,
        bytes: buffer,
        eof: offset.saturating_add(read as u64) >= file_len,
    })
}
