from sqlalchemy.orm import Session
import models, schemas
import bcrypt
from sqlalchemy import desc

SALT = b'$2b$12$0nFckzktMD0Fb16a8JsNA.'

def get_user(db: Session, id_user: int):
    return db.query(models.User).filter(models.User.id_user == id_user).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email_user == email).first()

def get_user_by_no_telp(db: Session, no_telp: str):
    return db.query(models.User).filter(models.User.no_telp_user == no_telp).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_relasi(db: Session, id_user: int):
    return db.query(models.Relasi).filter(models.Relasi.id_user == id_user).all()

def get_relasi_by_id(db: Session, id_relasi: int):
    return db.query(models.Relasi).filter(models.Relasi.id_relasi == id_relasi).first()

def get_dokter(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Dokter).offset(skip).limit(limit).all()

def get_dokter_by_id(db: Session, id_dokter: int):
    return db.query(models.Dokter).filter(models.Dokter.id_dokter == id_dokter).first()

def get_obat(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Obat).offset(skip).limit(limit).all()

def get_obat_by_id(db: Session, id_obat: int):
    return db.query(models.Obat).join(models.JenisObat).filter(models.Obat.id_obat == id_obat).first()

def get_jenis_obat_by_id(db: Session, id_jenis_obat: int):
    return db.query(models.JenisObat).filter(models.JenisObat.id_jenis_obat == id_jenis_obat).first()

def get_jadwal_dokter(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.JadwalDokter).offset(skip).limit(limit).all()

def get_jadwal_dokter_by_id(db: Session, id_dokter: int):
    return db.query(models.JadwalDokter).filter(models.JadwalDokter.id_dokter == id_dokter).order_by(models.JadwalDokter.tanggal_jadwal_dokter).all()

def get_janji_temu(db: Session, id_user: int):
    return db.query(models.JanjiTemu).filter(models.JanjiTemu.id_user == id_user).filter(models.JanjiTemu.status != "Selesai").order_by(models.JanjiTemu.tgl_janji_temu).all()

def get_janji_temu_by_id(db: Session, id_janji_temu: int):
    return db.query(models.JanjiTemu).filter(models.JanjiTemu.id_janji_temu == id_janji_temu).first()

def get_pengingat_minum_obat(db: Session, id_user: int):
    return db.query(models.PengingatMinumObat).filter(models.PengingatMinumObat.id_user == id_user).all()

def get_pengingat_minum_obat_by_id(db: Session, id_pengingat: int):
    return db.query(models.PengingatMinumObat).filter(models.PengingatMinumObat.id_pengingat == id_pengingat).first()


def hashPassword(passwd: str):
    bytePwd = passwd.encode('utf-8')
    pwd_hash = bcrypt.hashpw(bytePwd, SALT).decode('utf-8')
    return pwd_hash

# ######### user

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hashPassword(user.password_user)
    db_user = models.User(
        nama_lengkap_user=user.nama_lengkap_user,
        tgl_lahir_user=user.tgl_lahir_user,
        gender_user=user.gender_user[0],
        alamat_user=user.alamat_user,
        no_bpjs_user=user.no_bpjs_user,
        no_telp_user=user.no_telp_user,
        email_user=user.email_user,
        password_user=hashed_password,
        foto_user=user.foto_user,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, id_user: int, user_update: schemas.UserBase):
    user_update.gender_user = user_update.gender_user[0]
    db_user = db.query(models.User).filter(models.User.id_user == id_user).first()
    
    if not db_user:
        return None

    update_data = user_update.model_dump()
    update_data.pop('foto_user', None)
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_image_user(db: Session, id_user: int, filename: str):
    db_user = db.query(models.User).filter(models.User.id_user == id_user).first()
    
    if not db_user:
        return None
    
    print(db_user.nama_lengkap_user)
    db_user.foto_user = filename
    
    db.commit()
    db.refresh(db_user)
    print("foto_user = " + db_user.foto_user)
    
    return db_user.foto_user


def update_password(db: Session, id_user: int, newPassword: str):
    db_user = db.query(models.User).filter(models.User.id_user == id_user).first()
    if not db_user:
        return None
    
    hashed_password = hashPassword(newPassword)
    db_user.password_user = hashed_password
    db.commit()
    db.refresh(db_user)
    return db_user

## relasi
def create_relasi(db: Session, relasi: schemas.RelasiCreate):
    if relasi.foto_relasi == "":
        relasi.foto_relasi = "default.jpg"
    db_relasi = models.Relasi(
        id_user=relasi.id_user,
        nama_lengkap_relasi=relasi.nama_lengkap_relasi,
        no_bpjs_relasi=relasi.no_bpjs_relasi,
        tgl_lahir_relasi=relasi.tgl_lahir_relasi,
        gender_relasi=relasi.gender_relasi[0],
        no_telp_relasi=relasi.no_telp_relasi,
        alamat_relasi=relasi.alamat_relasi,
        foto_relasi=relasi.foto_relasi,
        tipe_relasi=relasi.tipe_relasi,
    )
    db.add(db_relasi)
    db.commit()
    db.refresh(db_relasi)
    return db_relasi

def update_image_relasi(db: Session, id_relasi: int, filename: str):
    db_relasi = db.query(models.Relasi).filter(models.Relasi.id_relasi == id_relasi).first()
    
    if not db_relasi:
        return None
    print(db_relasi.nama_lengkap_relasi)
    db_relasi.foto_relasi = filename
    
    db.commit()
    db.refresh(db_relasi)
    print("foto_relasi = " + db_relasi.foto_relasi)
    
    return db_relasi.foto_relasi

def delete_relasi_by_id(db: Session, id_relasi: int):
    hasil = db.query(models.Relasi).filter(models.Relasi.id_relasi == id_relasi).delete()
    db.commit()
    return {"record_dihapus":hasil} 

## dokter
def create_dokter(db: Session, dokter: schemas.DokterCreate):
    db_dokter = models.Dokter(
        nama_lengkap_dokter=dokter.nama_lengkap_dokter,
        spesialisasi_dokter=dokter.spesialisasi_dokter,
        lama_pengalaman_dokter=dokter.lama_pengalaman_dokter,
        alumnus_dokter=dokter.alumnus_dokter,
        harga_dokter=dokter.harga_dokter,
        minat_klinis_dokter=dokter.minat_klinis_dokter,
        foto_dokter=dokter.foto_dokter,
        rating_dokter=dokter.rating_dokter,
        id_poli=dokter.id_poli,
    )
    db.add(db_dokter)
    db.commit()
    db.refresh(db_dokter)
    return db_dokter

def delete_dokter_by_id(db: Session, id_dokter: int):
    hasil = db.query(models.Dokter).filter(models.Dokter.id_dokter == id_dokter).delete()
    db.commit()
    return {"record_dihapus":hasil} 

## obat
def create_obat(db: Session, obat: schemas.ObatCreate):
    db_obat = models.Obat(
        nama_obat=obat.nama_obat,
        deskripsi_obat=obat.deskripsi_obat,
        komposisi_obat=obat.komposisi_obat,
        dosis_obat=obat.dosis_obat,
        peringatan_obat=obat.peringatan_obat,
        efek_samping_obat=obat.efek_samping_obat,
        foto_obat=obat.foto_obat,
        id_jenis_obat=obat.id_jenis_obat,
    )
    db.add(db_obat)
    db.commit()
    db.refresh(db_obat)
    return db_obat

def delete_obat_by_id(db: Session, id_obat: int):
    hasil = db.query(models.Obat).filter(models.Obat.id_obat == id_obat).delete()
    db.commit()
    return {"record_dihapus":hasil} 

## janji_temu
def create_janji_temu(db: Session, janji_temu: schemas.JanjiTemuCreate):
    db_janji_temu = models.JanjiTemu(
        kode_janji_temu = janji_temu.kode_janji_temu,
        tgl_janji_temu = janji_temu.tgl_janji_temu,
        id_dokter = janji_temu.id_dokter,
        id_user = janji_temu.id_user,
        is_relasi = janji_temu.is_relasi,
        id_relasi = janji_temu.id_relasi,
        biaya_janji_temu = janji_temu.biaya_janji_temu,
        id_janji_temu_as_orang_lain = janji_temu.id_janji_temu_as_orang_lain,
        status = janji_temu.status
    )
    db.add(db_janji_temu)
    db.commit()
    db.refresh(db_janji_temu)
    return db_janji_temu

def alter_status(db: Session, id_janji_temu: int):
    # Fetch the current JanjiTemu record
    janji_temu = db.query(models.JanjiTemu).filter(models.JanjiTemu.id_janji_temu == id_janji_temu).one()
    
    # Define the sequence of status values
    status_sequence = [
        models.StatusEnum.MENUNGGU_AMBIL_ANTRIAN,
        models.StatusEnum.MENUNGGU_ANTRIAN,
        models.StatusEnum.DALAM_SESI,
        models.StatusEnum.MENUNGGU_PEMBAYARAN,
        models.StatusEnum.SELESAI
    ]
    
    # Get the current status
    current_status = janji_temu.status
    
    # Determine the next status value
    if current_status in status_sequence:
        current_index = status_sequence.index(current_status)
        if current_index < len(status_sequence) - 1:
            new_status = status_sequence[current_index + 1]
        else:
            new_status = status_sequence[current_index]  # Already at the last status, no change
    else:
        new_status = status_sequence[0]  # Default to the first status if current status is invalid
    
    # Update the status
    janji_temu.status = new_status
    
    # Commit the transaction
    db.commit()
    
    # Refresh the instance to reflect changes
    db.refresh(janji_temu)
    
    return janji_temu

## janji_temu
def create_janji_temu_as_orang_lain(db: Session, janji_temu_as_orang_lain: schemas.JanjiTemuAsOrangLainCreate):
    db_janji_temu_as_orang_lain = models.JanjiTemuAsOrangLain(
        nama_lengkap_orang_lain = janji_temu_as_orang_lain.nama_lengkap_orang_lain,
        no_bpjs_orang_lain = janji_temu_as_orang_lain.no_bpjs_orang_lain,
        tgl_lahir_orang_lain = janji_temu_as_orang_lain.tgl_lahir_orang_lain,
        gender_orang_lain = janji_temu_as_orang_lain.gender_orang_lain[0],
        no_telp_orang_lain = janji_temu_as_orang_lain.no_telp_orang_lain,
        alamat_orang_lain = janji_temu_as_orang_lain.alamat_orang_lain,
    )
    db.add(db_janji_temu_as_orang_lain)
    db.commit()
    db.refresh(db_janji_temu_as_orang_lain)
    return db_janji_temu_as_orang_lain

def delete_janji_temu_by_id(db: Session, id_janji_temu: int):
    hasil = db.query(models.JanjiTemu).filter(models.JanjiTemu.id_janji_temu == id_janji_temu).delete()
    db.commit()
    return {"record_dihapus":hasil} 

## pengingat_minum_obat
def create_pengingat_minum_obat(db: Session, pengingat_minum_obat: schemas.PengingatMinumObatCreate):
    db_pengingat_minum_obat = models.PengingatMinumObat(
        id_obat = pengingat_minum_obat.id_obat,
        id_user = pengingat_minum_obat.id_user,
        dosis = pengingat_minum_obat.dosis,
        sendok = pengingat_minum_obat.sendok,
        jadwal = pengingat_minum_obat.jadwal,
        aturan = pengingat_minum_obat.aturan,
    )
    db.add(db_pengingat_minum_obat)
    db.commit()
    db.refresh(db_pengingat_minum_obat)
    return db_pengingat_minum_obat


def get_rekam_medis_by_id(db: Session, rekam_medis_id: int):
    return db.query(models.RekamMedis).filter(models.RekamMedis.id_rekam_medis == rekam_medis_id).first()

def get_rekam_medis_selesai_by_user(db: Session, user_id: int):
    return db.query(models.RekamMedis).join(models.RekamMedis.janji_temu).filter(models.JanjiTemu.id_user == user_id, models.JanjiTemu.status == "Selesai").all()